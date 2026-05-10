# 🏗️ Arquitetura (A) - Estrutura e Fluxo do Projeto

Este arquivo define as diretrizes arquiteturais de alto nível para as IAs e desenvolvedores no repositório.

## 🗺️ Fluxograma Macro de Arquitetura (Mermaid)

```mermaid
graph TD
    subgraph Frontend [Next.js Web App]
        UI[Componentes UI] --> Hooks[Custom Hooks]
        Hooks --> API_Client[API Client Fetch/Axios]
    end

    subgraph Backend [NestJS API]
        API_Client --> Controller[Controllers HTTP/REST]
        Controller --> DTO[Validação DTO / Pipes]
        DTO --> Service[Services / Use Cases]
        Service --> Domain[Entidades / Domain Logic]
        Service --> Prisma[Prisma ORM]
    end

    subgraph Database [Dados]
        Prisma --> DB[(PostgreSQL)]
    end

    %% Regras de DDD e Desacoplamento
    subgraph Módulos DDD
        Mod_Budget[Módulo Orçamento]
        Mod_Inventory[Módulo Estoque]
        Mod_Budget -. Eventos/Injeção .-> Mod_Inventory
    end
    
    Service --> Módulos DDD
```

## 📐 Princípios de Design (Clean Arch & DDD)
- **Bounded Contexts:** Os módulos NestJS (ex: `BudgetModule`, `InventoryModule`) devem operar como contextos isolados.
- **Isolamento de Dados:** Um módulo não deve fazer queries diretas em tabelas de outro módulo. A comunicação deve ser feita pelos Services (via injeção de dependência) ou emissão de eventos.
- **Inversão de Dependência:** A lógica de domínio central não deve depender do framework (na medida do pragmatismo possível no NestJS).

## 📚 Documentação Modular e ADRs (Architecture Decision Records)
Para facilitar o **onboarding** e manter um histórico das decisões técnicas, o projeto utiliza documentação modular.

- Todas as documentações de módulos e regras de negócios específicas vivem na pasta `.ai/modules/`.
- **Sempre que um novo módulo for criado ou modificado significativamente, a IA DEVE:**
  1. Criar ou atualizar o arquivo do módulo em `.ai/modules/<nome-do-modulo>.md`.
  2. Registrar as decisões técnicas (Por que usamos X em vez de Y?) na seção de ADRs do arquivo.
  3. Atualizar o fluxograma Mermaid específico do módulo detalhando o fluxo de dados.
