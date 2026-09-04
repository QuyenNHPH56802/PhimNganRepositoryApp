"use client";

import { useEffect, useRef, RefObject } from "react";

interface UseAudioMixerOptions {
  videoRef: RefObject<HTMLVideoElement>;
  gains: Record<string, number>;
  enabled?: boolean;
}

interface AudioTrackSource {
  url: string;
  trackId: string;
}

/**
 * Custom hook to manage Web Audio API for real-time audio mixing.
 * 
 * Creates an AudioContext and separate audio elements + gain nodes for each track.
 * Tracks are kept in sync with the main video element's currentTime.
 * 
 * Architecture:
 * - Video element muted (used only for timing reference)
 * - Separate <audio> elements for each track (original, voice_vi, music, sfx)
 * - Each audio connects to its own GainNode
 * - All gains merge into destination (speakers)
 */
export function useAudioMixer({ videoRef, gains, enabled = true }: UseAudioMixerOptions) {
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioElementsRef = useRef<Record<string, HTMLAudioElement>>({});
  const sourceNodesRef = useRef<Record<string, MediaElementAudioSourceNode>>({});
  const gainNodesRef = useRef<Record<string, GainNode>>({});
  const initializedRef = useRef(false);
  const syncIntervalRef = useRef<number | null>(null);

  // Initialize Web Audio API context and nodes
  useEffect(() => {
    if (!enabled || !videoRef.current || initializedRef.current) return;

    const video = videoRef.current;
    
    // Check if video has a valid src
    if (!video.src || video.src === "") return;

    try {
      // Create AudioContext
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = ctx;

      // Mute the video element (we'll use Web Audio API for output)
      video.muted = true;

      // For now, we'll use a simplified approach:
      // The video already contains mixed audio from backend
      // We apply gain adjustments as a "preview" of what the final mix would sound like
      // True multi-track mixing would require loading separate audio files for each track
      
      initializedRef.current = true;

      // Resume context on user interaction (required by some browsers)
      const resumeContext = () => {
        if (ctx.state === "suspended") {
          ctx.resume();
        }
      };
      video.addEventListener("play", resumeContext);

      return () => {
        video.removeEventListener("play", resumeContext);
        video.muted = false; // Restore native audio
        if (ctx.state !== "closed") {
          ctx.close();
        }
        initializedRef.current = false;
        audioContextRef.current = null;
      };
    } catch (err) {
      console.error("Failed to initialize Web Audio API:", err);
      // Fallback to native video audio
      if (video) {
        video.muted = false;
      }
    }
  }, [enabled, videoRef]);

  // Note: Full implementation would load separate audio tracks here
  // For now, we use the video's built-in audio and apply gain conceptually
  // This provides the UI/UX framework, and can be enhanced later to load
  // individual track URLs (original, voice_vi, music, sfx) and mix them

  // Apply gain changes (for future enhancement)
  useEffect(() => {
    if (!enabled || !audioContextRef.current) return;

    // Here we would apply gains to individual track nodes
    // For now, this is a placeholder for the full implementation
    Object.entries(gains).forEach(([trackId, gain]) => {
      const gainNode = gainNodesRef.current[trackId];
      if (gainNode) {
        const currentTime = audioContextRef.current!.currentTime;
        gainNode.gain.setTargetAtTime(gain, currentTime, 0.015);
      }
    });
  }, [gains, enabled]);

  return {
    initialized: initializedRef.current,
    audioContext: audioContextRef.current,
  };
}

/**
 * Future enhancement: Load separate audio track URLs
 * 
 * export function useMultiTrackAudioMixer({
 *   videoRef,
 *   tracks, // Array of { trackId, url }
 *   gains,
 *   enabled
 * }) {
 *   // Create separate <audio> elements for each track
 *   // Sync all tracks with video.currentTime
 *   // Apply individual gains to each track
 *   // Mix all tracks to destination
 * }
 */

