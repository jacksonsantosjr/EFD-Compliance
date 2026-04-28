import React from 'react';
import { ArrowRight, ShieldCheck } from 'lucide-react';
import { heroImageBase64 } from '../assets/hero_image';

const Hero = ({ onAccess, isExiting }) => {
  return (
    <section className={`hero ${isExiting ? 'exit' : ''}`}>

      <div 
        className="hero-background" 
        style={{ backgroundImage: `url(${heroImageBase64})` }}
      ></div>
      <div className="hero-overlay"></div>
      
      <div className="hero-content">
        <div className="hero-badge">
          <ShieldCheck size={16} />
          <span>Inteligência em Conformidade</span>
        </div>
        <h1 className="hero-title">
          EFD Compliance <br />
          <span className="text-gradient">Hub de Auditoria Integrada</span>
        </h1>
        <p className="hero-subtitle">
          Plataforma avançada de auditoria pós-validação para EFD, ECD e ECF. 
          Garanta a integridade dos seus dados fiscais com validações e cruzamentos inteligentes e conformidade nível expert.
        </p>
        <div className="hero-actions">
          <button className="btn btn-primary btn-lg hero-btn" onClick={onAccess}>
            Acessar Plataforma
            <ArrowRight size={20} />
          </button>
        </div>
      </div>
    </section>
  );
};

export default Hero;
