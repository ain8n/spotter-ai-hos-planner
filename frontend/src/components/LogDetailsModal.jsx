import React, { useState } from 'react';
import { X, Check, FileText, Truck, Building, User, Package } from 'lucide-react';

export default function LogDetailsModal({ isOpen, onClose, headerDetails, onSave }) {
  const [formData, setFormData] = useState(headerDetails);

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = (e) => {
    e.preventDefault();
    onSave(formData);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileText size={20} color="#2563eb" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#0f172a' }}>
              Custom Daily Log Header Details
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSave}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <User size={14} /> Driver Full Name
              </label>
              <input
                type="text"
                className="form-input"
                name="driver_name"
                value={formData.driver_name}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Driver ID / Badge</label>
              <input
                type="text"
                className="form-input"
                name="driver_id"
                value={formData.driver_id}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <Building size={14} /> Carrier Name
            </label>
            <input
              type="text"
              className="form-input"
              name="carrier_name"
              value={formData.carrier_name}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Main Office Address</label>
            <input
              type="text"
              className="form-input"
              name="main_office_address"
              value={formData.main_office_address}
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Home Terminal Address</label>
            <input
              type="text"
              className="form-input"
              name="home_terminal_address"
              value={formData.home_terminal_address}
              onChange={handleChange}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <Truck size={14} /> Truck / Tractor Number
              </label>
              <input
                type="text"
                className="form-input"
                name="truck_tractor_num"
                value={formData.truck_tractor_num}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Trailer Number</label>
              <input
                type="text"
                className="form-input"
                name="trailer_num"
                value={formData.trailer_num}
                onChange={handleChange}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <Package size={14} /> Shipping B/L or Manifest
              </label>
              <input
                type="text"
                className="form-input"
                name="shipping_doc"
                value={formData.shipping_doc}
                onChange={handleChange}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Co-Driver Name</label>
              <input
                type="text"
                className="form-input"
                name="co_driver"
                value={formData.co_driver}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Shipper &amp; Commodity</label>
            <input
              type="text"
              className="form-input"
              name="shipper_commodity"
              value={formData.shipper_commodity}
              onChange={handleChange}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              style={{ width: 'auto', padding: '0.6rem 1.5rem' }}
            >
              <Check size={16} /> Save &amp; Apply Details
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
