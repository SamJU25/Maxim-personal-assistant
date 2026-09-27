import React, { useState, useRef, useEffect } from 'react';
import {
  Camera,
  Monitor,
  Maximize2,
  Minimize2,
  Power,
  Eye,
  AlertCircle,
  X,
  Scan,
  Check,
} from 'lucide-react';
import { VisualFeedType } from '../types';

export const VisualUplink: React.FC = () => {
  const [feedType, setFeedType] = useState<VisualFeedType>('standby');
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [streamResolution, setStreamResolution] = useState<{ width: number; height: number } | null>(null);
  const [hasSnapped, setHasSnapped] = useState<boolean>(false);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const captureFrameToChat = (e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!videoRef.current) return;
    const video = videoRef.current;
    if (video.videoWidth === 0 || video.videoHeight === 0) return;

    try {
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/jpeg', 0.88);

      const event = new CustomEvent('maxim:attach-perception-frame', {
        detail: {
          dataUrl,
          source: feedType,
          width: canvas.width,
          height: canvas.height,
          timestamp: new Date().toISOString(),
        },
      });
      window.dispatchEvent(event);

      setHasSnapped(true);
      setTimeout(() => setHasSnapped(false), 2000);
    } catch (err) {
      console.error('Failed to capture perception frame:', err);
    }
  };

  const stopActiveStream = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setFeedType('standby');
    setStreamResolution(null);
  };

  const startCamera = async () => {
    setErrorMsg(null);
    try {
      stopActiveStream();
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      streamRef.current = stream;
      setFeedType('camera');
      setIsModalOpen(false);

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(console.error);
      }

      const videoTrack = stream.getVideoTracks()[0];
      if (videoTrack) {
        const settings = videoTrack.getSettings();
        setStreamResolution({
          width: settings.width || 1280,
          height: settings.height || 720,
        });
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Camera permission denied or device not found.');
    }
  };

  const startScreenShare = async () => {
    setErrorMsg(null);
    try {
      stopActiveStream();
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: false,
      });
      streamRef.current = stream;
      setFeedType('screen');
      setIsModalOpen(false);

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(console.error);
      }

      const videoTrack = stream.getVideoTracks()[0];
      if (videoTrack) {
        const settings = videoTrack.getSettings();
        setStreamResolution({
          width: settings.width || 1920,
          height: settings.height || 1080,
        });
        videoTrack.onended = () => {
          stopActiveStream();
        };
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Screen share cancelled or not allowed.');
    }
  };

  // Re-attach stream if element re-renders
  useEffect(() => {
    if (feedType !== 'standby' && streamRef.current && videoRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [feedType, isExpanded]);

  useEffect(() => {
    return () => {
      stopActiveStream();
    };
  }, []);

  return (
    <>
      {/* Main Visual Uplink Card */}
      <div className="rounded-xl border border-border-subtle bg-bg-card p-4 transition-all shadow-sm flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-1.5 text-xs text-text-muted">
            <Eye className="w-3.5 h-3.5 text-text-secondary" />
            <span className="font-mono text-[11px] uppercase tracking-wider font-semibold text-text-secondary">
              Perception Feed
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider font-semibold border ${
                feedType === 'standby'
                  ? 'border-border-subtle text-text-muted bg-bg-card-subtle'
                  : 'border-accent/30 text-accent bg-accent/10'
              }`}
            >
              {feedType === 'standby' ? 'STANDBY' : feedType}
            </span>

            {feedType !== 'standby' && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1 rounded hover:bg-bg-card-hover text-text-secondary hover:text-text-primary transition-all cursor-pointer"
                title={isExpanded ? 'Collapse' : 'Expand View'}
              >
                {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
              </button>
            )}
          </div>
        </div>

        {/* Viewport Frame with Viewfinder Corner Reticles */}
        <div
          onClick={() => {
            if (feedType === 'standby') setIsModalOpen(true);
          }}
          className={`relative w-full ${
            feedType === 'standby' ? 'h-22 rounded-lg' : 'aspect-video rounded-md'
          } border border-border-subtle overflow-hidden bg-bg-card-subtle flex flex-col items-center justify-center transition-all ${
            feedType === 'standby'
              ? 'cursor-pointer hover:border-border-hover group'
              : ''
          }`}
        >
          {/* Subtle Viewfinder Corner Crosshairs */}
          <div className="absolute top-1.5 left-1.5 w-2 h-2 border-t border-l border-border-subtle group-hover:border-accent transition-colors z-20" />
          <div className="absolute top-1.5 right-1.5 w-2 h-2 border-t border-r border-border-subtle group-hover:border-accent transition-colors z-20" />
          <div className="absolute bottom-1.5 left-1.5 w-2 h-2 border-b border-l border-border-subtle group-hover:border-accent transition-colors z-20" />
          <div className="absolute bottom-1.5 right-1.5 w-2 h-2 border-b border-r border-border-subtle group-hover:border-accent transition-colors z-20" />

          {feedType === 'standby' ? (
            <div className="flex items-center gap-3 text-left px-3.5 z-10 w-full">
              <div className="w-8 h-8 rounded-lg border border-border-subtle bg-bg-card flex items-center justify-center text-text-muted group-hover:text-accent group-hover:border-accent/40 transition-all shadow-xs shrink-0">
                <Scan className="w-4 h-4 text-text-secondary group-hover:text-accent transition-colors" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-text-primary group-hover:underline truncate">
                  Click to Engage Uplink
                </p>
                <p className="text-[10px] text-text-muted font-mono uppercase tracking-wider truncate">
                  Optical Lens & Screen Stream
                </p>
              </div>
            </div>
          ) : (
            <div className="w-full h-full relative group">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />

              {/* Live Overlay HUD */}
              <div className="absolute top-2 left-2 flex items-center gap-1.5 px-2 py-0.5 rounded bg-black/75 backdrop-blur-sm border border-white/10 text-[10px] font-mono text-white">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="font-semibold">{feedType.toUpperCase()}</span>
                {streamResolution && (
                  <span className="text-white/70">
                    {streamResolution.width}×{streamResolution.height}
                  </span>
                )}
              </div>

              {/* Actions Overlay */}
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1.5 z-30">
                <button
                  onClick={captureFrameToChat}
                  className="flex items-center gap-1 px-2 py-1 rounded bg-accent/90 hover:bg-accent text-white text-[10px] font-mono shadow-sm transition-all cursor-pointer font-semibold"
                  title="Capture frame and attach to Chat for Vision AI analysis"
                >
                  {hasSnapped ? (
                    <>
                      <Check className="w-3 h-3 text-white" />
                      <span>ATTACHED</span>
                    </>
                  ) : (
                    <>
                      <Camera className="w-3 h-3" />
                      <span>SNAP TO CHAT</span>
                    </>
                  )}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    stopActiveStream();
                  }}
                  className="flex items-center gap-1 px-2 py-1 rounded bg-rose-600/90 hover:bg-rose-600 text-white text-[10px] font-mono shadow-sm transition-all cursor-pointer"
                  title="Disconnect Feed"
                >
                  <Power className="w-3 h-3" />
                  <span>STOP</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {errorMsg && (
          <div className="mt-2.5 flex items-center gap-1.5 text-xs text-rose-500 bg-rose-500/10 border border-rose-500/20 px-2.5 py-1.5 rounded-lg">
            <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="line-clamp-1">{errorMsg}</span>
          </div>
        )}
      </div>

      {/* Modal: Select Camera vs Screen Share */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-sm rounded-2xl border border-border-subtle bg-bg-card p-5 shadow-2xl transition-all">
            <div className="flex items-center justify-between pb-3 border-b border-border-subtle">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-text-primary" />
                <h3 className="text-sm font-semibold text-text-primary">Engage Visual Perception</h3>
              </div>
              <button
                onClick={() => {
                  setIsModalOpen(false);
                  setErrorMsg(null);
                }}
                className="p-1 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-card-hover"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-text-secondary mt-3 mb-4 leading-relaxed font-sans">
              Select an uplink source for MaxIM's computer vision and real-time environment perception.
            </p>

            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={startCamera}
                className="flex flex-col items-center justify-center p-4 rounded-xl border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover hover:border-border-active transition-all group active:scale-[0.98]"
              >
                <div className="w-10 h-10 rounded-full border border-border-subtle bg-bg-card flex items-center justify-center mb-2 group-hover:scale-105 transition-transform text-text-primary shadow-sm">
                  <Camera className="w-5 h-5" />
                </div>
                <span className="text-xs font-semibold text-text-primary">Camera Feed</span>
                <span className="text-[10px] text-text-muted font-mono mt-0.5">Physical Webcam</span>
              </button>

              <button
                onClick={startScreenShare}
                className="flex flex-col items-center justify-center p-4 rounded-xl border border-border-subtle bg-bg-card-subtle hover:bg-bg-card-hover hover:border-border-active transition-all group active:scale-[0.98]"
              >
                <div className="w-10 h-10 rounded-full border border-border-subtle bg-bg-card flex items-center justify-center mb-2 group-hover:scale-105 transition-transform text-text-primary shadow-sm">
                  <Monitor className="w-5 h-5" />
                </div>
                <span className="text-xs font-semibold text-text-primary">Screen Share</span>
                <span className="text-[10px] text-text-muted font-mono mt-0.5">Desktop / Window</span>
              </button>
            </div>

            {errorMsg && (
              <div className="mt-3 text-xs text-rose-500 bg-rose-500/10 border border-rose-500/20 px-2.5 py-1.5 rounded-lg flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Expanded Lightbox Modal when User Toggles Expand */}
      {isExpanded && feedType !== 'standby' && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-6 animate-in fade-in duration-200">
          <div className="w-full max-w-4xl rounded-2xl border border-border-subtle bg-bg-card p-4 shadow-2xl flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-border-subtle mb-3">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-sm font-semibold text-text-primary uppercase tracking-wider font-mono">
                  {feedType} Uplink • Full View
                </span>
                {streamResolution && (
                  <span className="text-xs font-mono text-text-muted">
                    ({streamResolution.width}×{streamResolution.height})
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={captureFrameToChat}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-accent hover:bg-accent/90 text-white text-xs font-mono shadow-sm transition-all cursor-pointer font-semibold"
                  title="Capture frame and attach to Chat for Vision AI analysis"
                >
                  {hasSnapped ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-white" />
                      <span>ATTACHED TO CHAT</span>
                    </>
                  ) : (
                    <>
                      <Camera className="w-3.5 h-3.5" />
                      <span>SNAP TO CHAT</span>
                    </>
                  )}
                </button>
                <button
                  onClick={() => setIsExpanded(false)}
                  className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-card-hover cursor-pointer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="w-full aspect-video rounded-xl overflow-hidden bg-black relative">
              <video
                ref={(el) => {
                  if (el && streamRef.current) {
                    el.srcObject = streamRef.current;
                    el.play().catch(console.error);
                  }
                }}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-contain"
              />
            </div>
          </div>
        </div>
      )}
    </>
  );
};
