import re

with open('static/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Add ID to Market History Section
c = c.replace(
    '''<div class="glass-card p-5 slide-up">
                        <div class="flex items-center gap-2 mb-4">
                            <svg class="w-5 h-5 text-indigo-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                            <h3 class="text-sm font-semibold text-white uppercase tracking-wide">Market History (this product)</h3>''',
    '''<div class="glass-card p-5 slide-up" id="marketHistorySection">
                        <div class="flex items-center gap-2 mb-4">
                            <svg class="w-5 h-5 text-indigo-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                            <h3 class="text-sm font-semibold text-white uppercase tracking-wide">Market History (this product)</h3>'''
)

# Add ID to Inquiry History Section
c = c.replace(
    '''<div class="glass-card p-5 slide-up">
                        <div class="flex items-center gap-2 mb-4">
                            <svg class="w-5 h-5 text-indigo-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/></svg>
                            <h3 class="text-sm font-semibold text-white uppercase tracking-wide">Inquiry History (this product)</h3>''',
    '''<div class="glass-card p-5 slide-up" id="inquiryHistorySection">
                        <div class="flex items-center gap-2 mb-4">
                            <svg class="w-5 h-5 text-indigo-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/></svg>
                            <h3 class="text-sm font-semibold text-white uppercase tracking-wide">Inquiry History (this product)</h3>'''
)

# Add is_custom flag in handleAnalyze
c = c.replace(
    'data.inquiry_history = [];',
    'data.inquiry_history = [];\n                        data.is_custom = true;'
)

# Use flag in renderResults
c = c.replace(
    "renderHistoryTable('inquiryHistoryBody',  d.inquiry_history,  ['enquiry_no', 'date', 'customer_name', 'rate', 'outcome']);",
    "renderHistoryTable('inquiryHistoryBody',  d.inquiry_history,  ['enquiry_no', 'date', 'customer_name', 'rate', 'outcome']);\n\n            if (d.is_custom) {\n                document.getElementById('marketHistorySection').style.display = 'none';\n                document.getElementById('inquiryHistorySection').style.display = 'none';\n            } else {\n                document.getElementById('marketHistorySection').style.display = 'block';\n                document.getElementById('inquiryHistorySection').style.display = 'block';\n            }"
)

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(c)

print('Update successful.')
