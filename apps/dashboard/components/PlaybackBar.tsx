"use client";

interface Props {
  currentStep: number;
  maxStep: number;
  playing: boolean;
  playbackSpeed: number;
  onStepChange: (step: number) => void;
  onTogglePlay: () => void;
  onSpeedChange: (speed: number) => void;
}

const SPEEDS = [0.5, 1, 2, 4] as const;

export default function PlaybackBar({
  currentStep,
  maxStep,
  playing,
  playbackSpeed,
  onStepChange,
  onTogglePlay,
  onSpeedChange,
}: Props) {
  return (
    <div className="flex items-center gap-3 border-t border-line bg-cream px-5 py-2.5 shrink-0">
      {/* play / pause */}
      <button
        type="button"
        onClick={onTogglePlay}
        disabled={maxStep === 0}
        className="w-7 h-7 flex items-center justify-center border border-line text-ink-soft hover:border-olive hover:text-olive transition-colors disabled:opacity-30"
        aria-label={playing ? "pause" : "play"}
      >
        {playing ? (
          /* pause bars */
          <svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor">
            <rect x="3" y="2" width="4" height="12" rx="1" />
            <rect x="9" y="2" width="4" height="12" rx="1" />
          </svg>
        ) : (
          /* play triangle */
          <svg viewBox="0 0 16 16" width="12" height="12" fill="currentColor">
            <path d="M4 2.5l9 5.5-9 5.5V2.5z" />
          </svg>
        )}
      </button>

      {/* step counter */}
      <span className="text-[11px] text-muted font-mono shrink-0 tabular-nums">
        step {currentStep} / {maxStep}
      </span>

      {/* scrubber */}
      <input
        type="range"
        min={0}
        max={maxStep}
        value={currentStep}
        onChange={(e) => onStepChange(Number(e.target.value))}
        className="flex-1 h-px accent-[#6B7C4A] cursor-pointer"
        style={{ accentColor: "var(--color-olive, #6B7C4A)" }}
      />

      {/* speed pills */}
      <div className="flex items-center gap-1 shrink-0">
        {SPEEDS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onSpeedChange(s)}
            className={`px-1.5 py-0.5 text-[10px] border lowercase tracking-[0.02em] transition-colors ${
              playbackSpeed === s
                ? "border-olive bg-olive text-white"
                : "border-line text-muted hover:border-olive hover:text-olive"
            }`}
          >
            {s}×
          </button>
        ))}
      </div>
    </div>
  );
}
