import { useNavigate } from 'react-router-dom'
import { FileText, Book, Building2 } from 'lucide-react'

function HubSelection() {
  const navigate = useNavigate()

  const cards = [
    {
      id: 'efd',
      title: 'EFD ICMS/IPI',
      description: 'SPED Fiscal. Auditoria de blocos C, E, G, H, K. Foco em ICMS, IPI e Inventário.',
      icon: <FileText size={48} color="#2f8fdd" />,
      theme: 'efd'
    },
    {
      id: 'ecd',
      title: 'ECD',
      description: 'Escrituração Contábil Digital. Validação de lançamentos, balancetes e partidas dobradas.',
      icon: <Book size={48} color="#059669" />,
      theme: 'ecd'
    },
    {
      id: 'ecf',
      title: 'ECF',
      description: 'Escrituração Contábil Fiscal. Cruzamentos avançados IRPJ e CSLL (Em breve).',
      icon: <Building2 size={48} color="#6C5CE7" />,
      theme: 'ecf'
    }
  ]

  return (
    <div className="hub-container">
      <div className="hub-header">
        <h1 className="hub-title">
          Hub de Auditoria Integrada
        </h1>
        <p className="hub-subtitle">
          Selecione a obrigação acessória para iniciar o processo de validação, cruzamento e geração do dossiê executivo.
        </p>
      </div>

      <div className="hub-grid">
        {cards.map(card => (
          <button
            key={card.id}
            onClick={() => navigate(`/upload/${card.id}`)}
            className={`hub-card card-${card.theme}`}
          >
            <div className="hub-card-icon-wrapper">
              {card.icon}
            </div>
            <div className="hub-card-content">
              <h3>{card.title}</h3>
              <p>{card.description}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

export default HubSelection

