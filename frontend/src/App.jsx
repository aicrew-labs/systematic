import { useState } from 'react';
import InputForm from './components/InputForm';
import ContextCards from './components/ContextCards';
import MarketSignals from './components/MarketSignals';
import PriceRange from './components/PriceRange';
import QuoteHistory from './components/QuoteHistory';
import DailyRatesModal from './components/DailyRatesModal';
import { getQuoteSuggestion } from './api/client';

export default function App() {
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const handleSubmit = async (formData) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await getQuoteSuggestion(formData);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1a1f3a 50%, #0f172a 100%)' }}>
      {/* Header */}
      <header className="border-b border-slate-800/50 backdrop-blur-md bg-slate-900/30 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                </svg>
              </div>
              <div>
                <h1 className="text-base font-bold text-white tracking-tight">Quote Intelligence</h1>
                <p className="text-[11px] text-slate-500">Systematic Industries Pvt Ltd</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-2">
                <span className="text-xs text-slate-500">Powered by AI</span>
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              </div>
              <button 
                onClick={() => setIsSettingsOpen(true)}
                className="w-9 h-9 rounded-xl bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700/50 flex items-center justify-center transition-colors"
                title="Daily Rates Settings"
              >
                <svg className="w-5 h-5 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Two-column layout on desktop */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left column — Input form */}
          <div className="lg:col-span-5">
            <div className="lg:sticky lg:top-24">
              <InputForm onSubmit={handleSubmit} isLoading={isLoading} />
            </div>
          </div>

          {/* Right column — Results */}
          <div className="lg:col-span-7 space-y-6">
            {/* Empty state */}
            {!result && !isLoading && !error && (
              <div className="glass-card-static p-12 text-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-purple-600/20 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Ready to Analyze</h3>
                <p className="text-sm text-slate-400 max-w-sm mx-auto">
                  Enter a customer enquiry on the left to get AI-powered pricing intelligence with real-time context.
                </p>
              </div>
            )}

            {/* Loading state */}
            {isLoading && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="glass-card-static p-5"><div className="shimmer h-20 rounded-lg" /></div>
                  ))}
                </div>
                <div className="glass-card-static p-6"><div className="shimmer h-32 rounded-lg" /></div>
              </div>
            )}

            {/* Error state */}
            {error && (
              <div className="glass-card-static p-6 border-rose-500/30">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-rose-500/20 flex items-center justify-center">
                    <svg className="w-5 h-5 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-rose-400">Error</p>
                    <p className="text-xs text-slate-400">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Results */}
            {result && (
              <>
                {result.context_cards && <ContextCards cards={result.context_cards} />}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {result.market_signal && <MarketSignals signals={[{type: 'Demand', message: result.market_signal, impact: 'neutral'}]} />}
                  {result.recent_quotes && result.recent_quotes.length > 0 && <QuoteHistory quotes={result.recent_quotes} />}
                </div>
                <PriceRange priceRange={{
                  recommended: result.recommended_price_mt,
                  floor: result.floor_price_mt,
                  target: result.target_price_mt,
                  base: result.base_cost_mt,
                  zinc: result.zinc_cost_mt,
                  conversion: result.conversion_cost_mt
                }} aiReasoning={result.pricing_logic_explanation} />
              </>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/30 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
          <p className="text-center text-xs text-slate-600">
            © 2026 Systematic Industries Pvt Ltd · Wire Manufacturing Intelligence Dashboard · v0.1
          </p>
        </div>
      </footer>

      {/* Modals */}
      <DailyRatesModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
    </div>
  );
}
