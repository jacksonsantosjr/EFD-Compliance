import { useEffect } from 'react';

function Modal({ isOpen, title, children, onClose }) {
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.4)',
      backdropFilter: 'blur(3px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999
    }}>
      <div className="card" style={{ 
        width: '450px', 
        maxWidth: '90%', 
        Animation: 'fadeIn 0.2s ease-out',
        boxShadow: '0 10px 25px rgba(0,0,0,0.2)' 
      }}>
        <div className="card-body">
          <h3 style={{ marginBottom: 'var(--space-4)', color: 'var(--color-text-primary)', fontSize: 'var(--font-size-lg)' }}>{title}</h3>
          <div style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-6)', lineHeight: 1.5, fontSize: 'var(--font-size-md)' }}>
            {children}
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn btn-primary" onClick={onClose} style={{ minWidth: '100px' }}>
              OK
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Modal;
