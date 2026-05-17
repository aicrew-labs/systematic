import { useState, useEffect } from 'react';

function formatPrice(n) {
  if (!n) return '—';
  return '₹' + Math.round(n).toLocaleString('en-IN');
}

export default function PriceRange({ priceRange, aiReasoning }) {
  const [showReasoning, setShowReasoning] = useState(false);
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    if (!aiReasoning) return;
    setShowReasoning(false);
    setDisplayedText('');
    const timer = setTimeout(() => {
      setShowReasoning(true);
      let idx = 0;
      const text = aiReasoning;
      const interval = setInterval(() => {
        idx += 2;
        if (idx >= text.length) { setDisplayedText(text); clearInterval(interval); }
        else { setDisplayedText(text.slice(0, idx)); }
      }, 10);
      return () => clearInterval(interval);
    }, 300);
    return () => clearTimeout(timer);
  }, [aiReasoning]);

  if (!priceRange) return null;
  const { recommended, floor, target, base, zinc, conversion } = priceRange;

  return (
    <div className="glass-card-static p-6 md:p-8 animate-fade-in-up" style={{ animationDelay: '0.2s', opacity: 0, animationFillMode: 'forwards' }}>
      <div className="flex items-center gap-2 mb-6">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
          </svg>
        </div>
        <h3 className="text-sm font-semibold text-white uppercase tracking-wide">Recommended Target Price</h3>
      </div>
      
      <div className="text-center mb-8">
        <div className="flex items-baseline justify-center gap-3">
          <span className="text-4xl md:text-5xl font-extrabold text-emerald-400 drop-shadow-md">{formatPrice(recommended)}</span>
        </div>
        <p className="text-sm text-slate-400 mt-2">per MT</p>
      </div>

      <div className="mb-6 p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3 border-b border-slate-700/50 pb-2">Cost Breakdown</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-300">Base Steel Cost</span>
            <span className="text-slate-200 font-medium">{formatPrice(base)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-300">Zinc Cost (Formula)</span>
            <span className="text-slate-200 font-medium">+{formatPrice(zinc)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-300">Conversion Cost</span>
            <span className="text-slate-200 font-medium">+{formatPrice(conversion)}</span>
          </div>
          <div className="border-t border-slate-700 my-2 pt-2 flex justify-between font-bold">
            <span className="text-slate-200">Floor Cost</span>
            <span className="text-rose-400">{formatPrice(floor)}</span>
          </div>
          <div className="flex justify-between font-bold pt-1">
            <span className="text-slate-200">Standard Target (w/ margin)</span>
            <span className="text-indigo-400">{formatPrice(target)}</span>
          </div>
        </div>
      </div>

      {showReasoning && (
        <div className="mt-4 p-4 rounded-xl bg-slate-900/50 border border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.1)]">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" /></svg>
            <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wide">Pricing Logic</span>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed">
            {displayedText}
            {displayedText.length < (aiReasoning?.length || 0) && <span className="inline-block w-0.5 h-4 bg-indigo-400 ml-0.5 animate-pulse align-middle" />}
          </p>
        </div>
      )}
    </div>
  );
}
