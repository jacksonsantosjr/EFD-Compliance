import React, { useState } from 'react';
import { X, Mail, Lock, User, ArrowRight, RefreshCcw } from 'lucide-react';
import { supabase } from '../services/supabase';

const LoginModal = ({ isOpen, onClose, onLoginSuccess }) => {
  const [view, setView] = useState('login'); // 'login' | 'signup' | 'reset'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);

  if (!isOpen) return null;

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      onLoginSuccess(data.user);
    } catch (err) {
      setError(err.message || 'Erro ao fazer login. Verifique suas credenciais.');
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: { data: { full_name: name } }
      });
      if (error) throw error;
      setMessage('Conta criada com sucesso! Verifique seu e-mail para confirmar.');
    } catch (err) {
      setError(err.message || 'Erro ao criar conta.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email);
      if (error) throw error;
      setMessage('Link de recuperação enviado para seu e-mail.');
    } catch (err) {
      setError(err.message || 'Erro ao enviar link de recuperação.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} style={{ animation: 'overlayFadeIn 0.8s ease-out' }}>
      <div 
        className="card login-modal" 
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '400px',
          maxWidth: '95%',
          background: 'var(--color-bg-elevated)',
          backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          boxShadow: 'var(--shadow-xl)',
          animation: 'modalDropDown 1.2s cubic-bezier(0.16, 1, 0.3, 1)'
        }}
      >
        <div className="card-header" style={{ borderBottom: 'none', paddingBottom: 0 }}>
          <h2 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 'var(--font-weight-bold)', color: 'var(--color-bg-accent)' }}>
            {view === 'login' ? '🔐 Acesso Restrito' : view === 'signup' ? '📝 Criar Conta' : '🔄 Recuperar Senha'}
          </h2>
          <button className="btn-icon" onClick={onClose}><X size={20} /></button>
        </div>

        <div className="card-body" style={{ padding: 'var(--space-12) var(--space-10)' }}>
          {error && <div className="badge badge-critical mb-10" style={{ width: '100%', padding: 'var(--space-3)' }}>{error}</div>}
          {message && <div className="badge badge-success mb-10" style={{ width: '100%', padding: 'var(--space-3)' }}>{message}</div>}

          <form onSubmit={view === 'login' ? handleLogin : view === 'signup' ? handleSignUp : handleResetPassword}>
            {view === 'signup' && (
              <div className="flex flex-col gap-4 mb-10">
                <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-secondary)', letterSpacing: '0.08em' }}>NOME COMPLETO</label>
                <div style={{ position: 'relative' }}>
                  <User size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-tertiary)' }} />
                  <input 
                    type="text" 
                    className="btn btn-secondary" 
                    style={{ width: '100%', paddingLeft: '48px', height: '54px', textAlign: 'left', background: 'var(--color-bg-tertiary)' }}
                    placeholder="Seu nome"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
              </div>
            )}

            <div className="flex flex-col gap-4 mb-10">
              <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-secondary)', letterSpacing: '0.08em' }}>E-MAIL</label>
              <div style={{ position: 'relative' }}>
                <Mail size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-tertiary)' }} />
                <input 
                  type="email" 
                  className="btn btn-secondary" 
                  style={{ width: '100%', paddingLeft: '48px', height: '54px', textAlign: 'left', background: 'var(--color-bg-tertiary)' }}
                  placeholder="seu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            {view !== 'reset' && (
              <div className="flex flex-col gap-4 mb-12">
                <div className="flex justify-between items-center">
                  <label style={{ fontSize: 'var(--font-size-xs)', fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-secondary)', letterSpacing: '0.08em' }}>SENHA</label>
                  {view === 'login' && (
                    <button 
                      type="button" 
                      onClick={() => setView('reset')}
                      style={{ background: 'none', border: 'none', color: 'var(--color-bg-accent)', fontSize: 'var(--font-size-xs)', cursor: 'pointer', fontWeight: 'var(--font-weight-medium)' }}
                    >
                      Esqueceu a senha?
                    </button>
                  )}
                </div>
                <div style={{ position: 'relative' }}>
                  <Lock size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-tertiary)' }} />
                  <input 
                    type="password" 
                    className="btn btn-secondary" 
                    style={{ width: '100%', paddingLeft: '48px', height: '54px', textAlign: 'left', background: 'var(--color-bg-tertiary)' }}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>
              </div>
            )}

            <button 
              type="submit" 
              className="btn btn-primary" 
              style={{ width: '100%', height: '58px', gap: 'var(--space-2)', fontSize: 'var(--font-size-md)', borderRadius: 'var(--radius-lg)', fontWeight: 'var(--font-weight-bold)' }}
              disabled={loading}
            >
              {loading ? <RefreshCcw className="spinner" size={20} /> : (
                <>
                  {view === 'login' ? 'Entrar' : view === 'signup' ? 'Cadastrar' : 'Enviar Link'}
                  <ArrowRight size={20} />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 text-center" style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-tertiary)' }}>
            {view === 'login' ? (
              <>
                Não tem uma conta?{' '}
                <button 
                  onClick={() => setView('signup')}
                  style={{ background: 'none', border: 'none', color: 'var(--color-bg-accent)', fontWeight: 'var(--font-weight-semibold)', cursor: 'pointer' }}
                >
                  Criar conta agora
                </button>
              </>
            ) : (
              <button 
                onClick={() => setView('login')}
                style={{ background: 'none', border: 'none', color: 'var(--color-bg-accent)', fontWeight: 'var(--font-weight-semibold)', cursor: 'pointer' }}
              >
                Voltar para o Login
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginModal;
