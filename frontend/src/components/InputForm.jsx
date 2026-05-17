import { useState, useEffect, useRef } from 'react';
import { getCustomers, getProducts } from '../api/client';

const PAYMENT_TERMS = ['Advance', '30 Days', '45 Days', '60 Days'];
const APPLICATIONS = ['Fencing', 'Cable Armouring', 'Wire Mesh', 'Nails', 'General Engineering', 'Other'];
const LOCATIONS = ['Gujarat', 'Maharashtra', 'Delhi', 'South India', 'Export', 'Other'];

export default function InputForm({ onSubmit, isLoading }) {
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  
  const [customerQuery, setCustomerQuery] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);

  const [form, setForm] = useState({
    customer_id: '',
    customer_type: 'Old',
    product_type: '',
    product_code: '',
    diameter_mm: '',
    zinc_coating_gsm: '',
    tensile_strength: 'Medium',
    quantity_mt: '',
    application: '',
    location: '',
    payment_terms: '30 Days',
  });

  // Load initial data
  useEffect(() => {
    getCustomers().then(setCustomers).catch(console.error);
    getProducts().then(setProducts).catch(console.error);
  }, []);

  // Filter customers for dropdown
  const filteredCustomers = customerQuery.length > 1 
    ? customers.filter(c => c.name.toLowerCase().includes(customerQuery.toLowerCase())).slice(0, 5)
    : [];

  // Get unique product types
  const productTypes = [...new Set(products.map(p => p.product_type))].filter(Boolean);
  
  // Get product codes for selected type
  const productCodes = form.product_type 
    ? products.filter(p => p.product_type === form.product_type).map(p => p.product_code)
    : [];

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const selectCustomer = (customer) => {
    setForm(f => ({ ...f, customer_id: customer.customer_id, customer_type: 'Old' }));
    setCustomerQuery(customer.name);
    setShowDropdown(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Allow submitting new customer without ID
    const submitData = {
      ...form,
      customer_id: form.customer_type === 'New' ? 'NEW_CUST' : form.customer_id,
      diameter_mm: form.diameter_mm ? parseFloat(form.diameter_mm) : 2.0,
      zinc_coating_gsm: form.zinc_coating_gsm ? parseFloat(form.zinc_coating_gsm) : 60.0,
      quantity_mt: parseFloat(form.quantity_mt)
    };
    onSubmit(submitData);
  };

  const isValid = (form.customer_id || form.customer_type === 'New') && 
                  form.product_type && 
                  form.product_code && 
                  form.quantity_mt > 0;

  return (
    <div className="glass-card-static p-6 md:p-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-semibold text-white">Quote parameters</h2>
          <p className="text-xs text-slate-400">Enter technical & commercial details</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          
          {/* Customer Type Toggle */}
          <div className="md:col-span-2 flex gap-4 p-1 bg-slate-800/50 rounded-lg w-fit">
            <button type="button" onClick={() => setForm({...form, customer_type: 'Old'})} 
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${form.customer_type === 'Old' ? 'bg-indigo-500 text-white' : 'text-slate-400 hover:text-white'}`}>
              Existing Customer
            </button>
            <button type="button" onClick={() => setForm({...form, customer_type: 'New', customer_id: ''})} 
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${form.customer_type === 'New' ? 'bg-indigo-500 text-white' : 'text-slate-400 hover:text-white'}`}>
              New Customer
            </button>
          </div>

          {/* Customer Name */}
          <div className="md:col-span-2 relative" ref={dropdownRef}>
            <label className="form-label">Customer Name</label>
            {form.customer_type === 'Old' ? (
              <>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Search existing customer..."
                  value={customerQuery}
                  onChange={(e) => {
                    setCustomerQuery(e.target.value);
                    if(e.target.value === '') setForm(f => ({...f, customer_id: ''}));
                  }}
                  onFocus={() => filteredCustomers.length > 0 && setShowDropdown(true)}
                />
                {showDropdown && filteredCustomers.length > 0 && (
                  <div className="search-dropdown z-50 absolute w-full mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl overflow-hidden">
                    {filteredCustomers.map((c) => (
                      <div
                        key={c.customer_id}
                        className="px-4 py-3 hover:bg-slate-700 cursor-pointer text-slate-200 border-b border-slate-700/50 last:border-0"
                        onClick={() => selectCustomer(c)}
                      >
                        {c.name}
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <input type="text" className="form-input" placeholder="Enter new customer name..." required />
            )}
          </div>

          {/* Product Type & Code */}
          <div>
            <label className="form-label">Product Type</label>
            <select
              className="form-select"
              value={form.product_type}
              onChange={(e) => setForm(f => ({ ...f, product_type: e.target.value, product_code: '' }))}
              required
            >
              <option value="">Select type...</option>
              {productTypes.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="form-label">Product / Size</label>
            <select
              className="form-select"
              value={form.product_code}
              onChange={(e) => setForm(f => ({ ...f, product_code: e.target.value }))}
              disabled={!form.product_type}
              required
            >
              <option value="">Select product...</option>
              {productCodes.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          {/* Technical Specs: Diameter & Zinc */}
          <div>
            <label className="form-label">Diameter (mm)</label>
            <input
              type="number"
              className="form-input"
              placeholder="e.g. 2.50"
              step="0.01"
              value={form.diameter_mm}
              onChange={(e) => setForm(f => ({ ...f, diameter_mm: e.target.value }))}
            />
          </div>
          <div>
            <label className="form-label">Zinc Coating (GSM)</label>
            <input
              type="number"
              className="form-input"
              placeholder="e.g. 60, 90, 275"
              value={form.zinc_coating_gsm}
              onChange={(e) => setForm(f => ({ ...f, zinc_coating_gsm: e.target.value }))}
            />
          </div>

          {/* Tensile & Quantity */}
          <div>
            <label className="form-label">Tensile Strength</label>
            <select
              className="form-select"
              value={form.tensile_strength}
              onChange={(e) => setForm(f => ({ ...f, tensile_strength: e.target.value }))}
            >
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Extra High">Extra High</option>
            </select>
          </div>
          <div>
            <label className="form-label">Quantity (MT)</label>
            <input
              type="number"
              className="form-input"
              placeholder="e.g. 25"
              min="0.1"
              step="0.1"
              value={form.quantity_mt}
              onChange={(e) => setForm(f => ({ ...f, quantity_mt: e.target.value }))}
              required
            />
          </div>

          {/* Commercials: App, Location, Terms */}
          <div className="md:col-span-2 grid grid-cols-1 md:grid-cols-3 gap-5">
            <div>
              <label className="form-label">Application</label>
              <select className="form-select" value={form.application} onChange={e => setForm(f => ({...f, application: e.target.value}))}>
                <option value="">Select...</option>
                {APPLICATIONS.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
            <div>
              <label className="form-label">Location</label>
              <select className="form-select" value={form.location} onChange={e => setForm(f => ({...f, location: e.target.value}))}>
                <option value="">Select...</option>
                {LOCATIONS.map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            </div>
            <div>
              <label className="form-label">Payment Terms</label>
              <select className="form-select" value={form.payment_terms} onChange={e => setForm(f => ({...f, payment_terms: e.target.value}))}>
                {PAYMENT_TERMS.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="mt-8 flex justify-end">
          <button type="submit" className="btn-primary w-full md:w-auto" disabled={!isValid || isLoading}>
            {isLoading ? 'Analyzing...' : 'Generate AI Quote'}
          </button>
        </div>
      </form>
    </div>
  );
}
