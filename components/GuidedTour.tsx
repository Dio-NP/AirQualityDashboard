"use client";
import * as React from 'react';

type Step = {
  selector: string;
  title: string;
  body: string;
};

export default function GuidedTour({ steps, onClose }: { steps: Step[]; onClose: () => void }) {
  const [index, setIndex] = React.useState(0);
  const current = steps[index];
  const target = current ? document.querySelector(current.selector) as HTMLElement | null : null;
  const rect = target?.getBoundingClientRect();

  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowRight') setIndex(i => Math.min(i + 1, steps.length - 1));
      if (e.key === 'ArrowLeft') setIndex(i => Math.max(i - 1, 0));
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [steps.length, onClose]);

  if (!current) return null;

  return (
    <div className="fixed inset-0 z-50">
      {/* dimmer */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* highlight box */}
      {rect && (
        <div
          className="absolute border-2 border-blue-500 rounded pointer-events-none"
          style={{ left: rect.left - 6, top: rect.top - 6, width: rect.width + 12, height: rect.height + 12 }}
        />
      )}

      {/* tooltip */}
      <div
        className="absolute bg-white shadow-lg rounded p-4 w-[320px] text-sm"
        style={{ left: (rect?.left ?? 40), top: (rect ? rect.bottom + 10 : 40) }}
      >
        <div className="font-semibold mb-1">{current.title}</div>
        <div className="text-gray-700 mb-3">{current.body}</div>
        <div className="flex items-center justify-between">
          <button className="px-2 py-1 bg-gray-200 rounded" onClick={() => setIndex(i => Math.max(i - 1, 0))} disabled={index === 0}>Back</button>
          <div className="text-xs text-gray-500">{index + 1} / {steps.length}</div>
          {index < steps.length - 1 ? (
            <button className="px-2 py-1 bg-blue-600 text-white rounded" onClick={() => setIndex(i => Math.min(i + 1, steps.length - 1))}>Next</button>
          ) : (
            <button className="px-2 py-1 bg-green-600 text-white rounded" onClick={onClose}>Finish</button>
          )}
        </div>
      </div>
    </div>
  );
}


