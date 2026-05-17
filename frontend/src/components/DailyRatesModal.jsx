import { useState, useEffect } from 'react';
import { getDailyRates, setDailyRates } from '../api/client';

export default function DailyRatesModal({ isOpen, onClose }) {
  const [rates, setRates] = useState({
    steel_ms_rate: 0,
    steel_hc_rate: 0,
    zinc_rate: 0,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadRates();
    }
  }, [isOpen]);

  const loadRates = async () => {
    try {
      const data = await getDailyRates();
      setRates(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      await setDailyRates({
        steel_ms_rate: Number(rates.steel_ms_rate),
        steel_hc_rate: Number(rates.steel_hc_rate),
        zinc_rate: Number(rates.zinc_rate),
      });
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-md p-6 shadow-2xl">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-white">Daily RM Rates</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        
        {error && <div className="mb-4 p-3 bg-rose-500/20 border border-rose-500/50 rounded-lg text-rose-300 text-sm">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">MS Steel Rate (₹/MT)</label>
            <input
              type="number"
              value={rates.steel_ms_rate}
              onChange={(e) => setRates({ ...rates, steel_ms_rate: e.target.value })}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">HC Steel Rate (₹/MT)</label>
            <input
              type="number"
              value={rates.steel_hc_rate}
              onChange={(e) => setRates({ ...rates, steel_hc_rate: e.target.value })}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Zinc Rate (₹/KG)</label>
            <input
              type="number"
              value={rates.zinc_rate}
              onChange={(e) => setRates({ ...rates, zinc_rate: e.target.value })}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500"
              required
            />
          </div>
          
          <div className="pt-4 flex justify-end gap-3">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-xl text-slate-300 hover:bg-slate-800">
              Cancel
            </button>
            <button type="submit" disabled={isLoading} className="px-4 py-2 rounded-xl bg-indigo-500 hover:bg-indigo-600 text-white font-medium">
              {isLoading ? 'Saving...' : 'Save Rates'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
