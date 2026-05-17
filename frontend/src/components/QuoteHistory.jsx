export default function QuoteHistory({ quotes }) {
  if (!quotes || quotes.length === 0) return null;

  return (
    <div className="glass-card-static p-6 animate-fade-in-up" style={{ animationDelay: '0.5s', opacity: 0, animationFillMode: 'forwards' }}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-sm font-semibold text-white uppercase tracking-wide">Recent Quote History</h3>
        </div>
        <span className="text-xs text-slate-500">Last 5 quotes for this product</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="text-left py-3 px-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">Date</th>
              <th className="text-left py-3 px-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">Customer</th>
              <th className="text-right py-3 px-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">Rate</th>
              <th className="text-right py-3 px-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">Qty</th>
              <th className="text-center py-3 px-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">Outcome</th>
            </tr>
          </thead>
          <tbody>
            {quotes.map((q, i) => {
              const d = new Date(q.quote_date);
              const dateStr = d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
              return (
                <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-2 text-slate-300 whitespace-nowrap">{dateStr}</td>
                  <td className="py-3 px-2 text-slate-200 max-w-[200px] truncate">{q.customer_name}</td>
                  <td className="py-3 px-2 text-right text-white font-medium whitespace-nowrap">
                    ₹{Math.round(q.unit_rate_inr).toLocaleString('en-IN')}/{q.unit}
                  </td>
                  <td className="py-3 px-2 text-right text-slate-300 whitespace-nowrap">
                    {q.quantity} {q.unit}
                  </td>
                  <td className="py-3 px-2 text-center">
                    <span className={q.outcome === 'won' ? 'badge-won' : 'badge-lost'}>
                      {q.outcome === 'won' ? '✓ Won' : '✗ Lost'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
