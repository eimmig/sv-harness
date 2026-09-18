---
tags: [business, identity, tenancy]
---

# Tenant e usuários

## Objetivo

Representar uma organização com vários usuários independentes. O tenant é o limite de isolamento dos dados de negócio; usuário não é sinônimo de tenant.

## Regras

- O tenant é criado pelo operador da plataforma, sem autocadastro público.
- A criação provisiona o schema `tenant_<slug>` nos três serviços com banco.
- O primeiro usuário é `admin`, recebe senha temporária e `mustChangePassword`.
- Um `admin` pode criar membros e gerenciar usuários do próprio tenant.
- Um tenant nunca fica sem admin: rebaixar o único admin é rejeitado.
- E-mail é único apenas dentro do tenant.
- A senha temporária não bloqueia o login; após autenticar, o usuário pode usar a troca de senha.

## Limites e relações

[[auth-service]] é dono de usuários e do diretório global Telegram. [[bets-service]] e [[stats-service]] não possuem a tabela de usuários: recebem identidade e tenant pelos contratos de confiança. O isolamento técnico está em [[modelo-de-dados]] e [[convencoes]].

## Requisitos e contratos

- RF01, RF02: [[requisitos]]
- Fluxos e endpoints: [[autenticacao-e-acesso]] e [[contratos-de-api]]
- Decisões que alteraram o TCC1: [[DECISIONS-LOG]]
