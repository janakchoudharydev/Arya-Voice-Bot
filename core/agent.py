"""
ARYA Voice Agent - Mac Mini M1 AI Assistant

Uses LiveKit AgentSession with Gemini Realtime for voice interaction.
Particle visualization syncs with speaking state via agent_state_changed events.
"""
import logging
import asyncio
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.plugins import (google, noise_cancellation)
import sys
import os
# Add project root to path so we can import from 'tools' and 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json


from tools.mac_tools import ALL_MAC_TOOLS  # Import all Mac control tools
from tools.tools import ADDITIONAL_TOOLS  # Import additional tools
from tools.research_tools import RESEARCH_TOOLS  # Import research tools
from tools.browser_tools import BROWSER_TOOLS  # Import browser tools
from core.visualizer import OrbVisualizer
from core.instructions import ARYA_INSTRUCTIONS

# Combine all tools
ALL_TOOLS = ALL_MAC_TOOLS + ADDITIONAL_TOOLS + RESEARCH_TOOLS + BROWSER_TOOLS

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Root Files", ".env")
load_dotenv(env_path)

# Configure production-level logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d [%(name)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("arya-agent")
logger.setLevel(logging.DEBUG)

# Patch LiveKit SDK for known KeyError race condition
try:
    _orig_on_room_event = rtc.Room._on_room_event
    
    def _patched_on_room_event(self, event):
        try:
            _orig_on_room_event(self, event)
        except KeyError as e:
            if len(e.args) > 0 and isinstance(e.args[0], str) and e.args[0].startswith("TR_"):
                logger.warning(
                    "⚠️ Suppressed known LiveKit SDK KeyError for track %s. "
                    "This is a harmless race condition.", e
                )
            else:
                raise
                
    rtc.Room._on_room_event = _patched_on_room_event
    logger.info("✅ Applied LiveKit SDK KeyError patch.")
except Exception as e:
    logger.error("Failed to apply LiveKit SDK patch: %s", e)


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=ARYA_INSTRUCTIONS)


server = AgentServer()


@server.rtc_session()
async def my_agent(ctx: agents.JobContext):
    await ctx.connect()
    
    # --- VISUALIZER SETUP ---
    visualizer = OrbVisualizer()
    visualizer.start()
    
    # Publish Video Track (Visualizer)
    video_track = rtc.LocalVideoTrack.create_video_track("agent_video", visualizer.source)
    await ctx.room.local_participant.publish_track(video_track, rtc.TrackPublishOptions(
        source=rtc.TrackSource.SOURCE_CAMERA
    ))
    logger.info("🎥 Visualizer video track published")
    
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            voice="Puck",  # Gemini 'Bro' sounding voice
            instructions=ARYA_INSTRUCTIONS, # Strongly inject personality here
        ),
        tools=ALL_TOOLS,  # All tools: Mac controls + WhatsApp + Weather + Search + Email
    )
    
    # ==========================================================================
    # SPEAKING STATE DETECTION - Zero-lag via agent_state_changed
    # ==========================================================================
    
    @session.on("agent_state_changed")
    def on_agent_state_changed(event):
        """
        Triggered when agent state changes.
        States: initializing -> listening -> thinking -> speaking -> listening
        """
        old_state = event.old_state
        new_state = event.new_state
        
        logger.info("🎭 Agent state: %s → %s", old_state, new_state)
        
        # Update Visualizer
        visualizer.set_state(str(new_state))
        
        # Broadcast state to frontend visualizer
        payload = json.dumps({"type": "state", "value": str(new_state)})
        asyncio.create_task(ctx.room.local_participant.publish_data(payload, reliable=True))
        

    
    # ==========================================================================
    # USER STATE DETECTION - Block animation during user speech
    # ==========================================================================
    
    @session.on("user_state_changed")
    def on_user_state_changed(event):
        """
        Triggered when user state changes (speaking, listening, away).
        
        Used to ensure animation doesn't activate if user is speaking
        (prevents false triggers from echo/feedback).
        """
        old_state = event.old_state
        new_state = event.new_state
        
        logger.debug(
            "👤 User state: %s → %s",
            old_state.name if hasattr(old_state, 'name') else old_state,
            new_state.name if hasattr(new_state, 'name') else new_state
        )
    
    # ==========================================================================
    # INTERRUPTION HANDLING - Immediate animation stop on interruption
    # ==========================================================================
    
    @session.on("agent_speech_interrupted")
    def on_speech_interrupted(event):
        """Triggered when user interrupts ARYA's speech."""
        visualizer.set_state("listening")

    
    # ==========================================================================
    # METRICS LOGGING - Debug performance issues on Mac Mini M1
    # ==========================================================================
    
    @session.on("metrics_collected")
    def on_metrics_collected(event):
        """Log metrics for debugging latency/performance issues."""
        metrics = event.metrics
        metrics_type = type(metrics).__name__
        
        # Log TTS metrics for audio latency debugging
        if hasattr(metrics, 'ttfb'):
            logger.debug(
                "📈 %s: TTFB=%.0fms, duration=%.0fms",
                metrics_type,
                getattr(metrics, 'ttfb', 0) * 1000,
                getattr(metrics, 'duration', 0) * 1000
            )
    
    # Start the agent session
    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony() 
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP 
                    else noise_cancellation.BVC()
                ),
            ),
            video_input=False,
        ),
    )
    

    
    # Initial Welcome
    await session.generate_reply(
        instructions="Greet Janak in a very cool Hinglish 'Bro' tone. Tell him Arya is online, sorted hai, and ready to help build the empire."
    )
    
    # Keep agent alive
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await visualizer.stop()


if __name__ == "__main__":
    agents.cli.run_app(server)