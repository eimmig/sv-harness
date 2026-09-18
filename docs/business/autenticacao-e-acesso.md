---
tags: [business, security, api]
---

# Autenticação e acesso

## Jornada principal

1. O usuário informa `slug`, e-mail e senha.
2. [[auth-service]] valida a conta no schema do tenant.
3. O serviço emite PASETO v4.local com `userId`, `tenantId`, `iat` e `exp`.
4. [[api-gateway]] valida o token e injeta `X-User-Id`, `X-Tenant-Id` e `X-User-Role` nos serviços internos.
5. O frontend mantém apenas o contexto necessário para a sessão; não decodifica o token simétrico.

## Regras de segurança

- Login inválido retorna o mesmo erro para slug, e-mail ou senha incorretos.
- O token dura 8 horas e não há refresh token no escopo atual.
- `admin` libera gestão de usuários e configurações administrativas; `member` não vê essas áreas.
- A troca de senha exige sessão e senha atual; sucesso limpa `mustChangePassword`.
- A credencial administrativa de provisionamento não é credencial de usuário.

## Interfaces relacionadas

[[contratos-de-api]] documenta payloads, erros e headers. [[observabilidade-e-configuracao]] documenta chaves e variáveis. [[tenant-e-usuarios]] explica a regra de tenancy. [[jornadas-da-aplicacao-web]] descreve a experiência de login e autorização na UI.
