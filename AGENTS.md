# Regras de trabalho do AtendeAI

- Use `instrucoes_desafio.md` como referência dos requisitos iniciais do desafio, não como comprovação do que está implementado; confira o código e a documentação atual. Consulte `PLANO_IMPLEMENTACAO.md` para a fase e o estado do trabalho.
- Atue como engenheiro de software: inspecione o estado atual antes de alterar arquivos, entenda o impacto, preserve trabalho existente e implemente incrementalmente.
- Siga a arquitetura e os critérios do desafio; mantenha o backend como fonte da verdade e contratos claros entre frontend, API, IA e n8n.
- Não invente integrações ou dados reais. Não exponha segredos; use variáveis de ambiente e mantenha `.env` fora do Git.
- Ao validar a configuração do Compose em ambiente com `.env`, use `docker compose config --quiet`; nunca execute a forma detalhada (`docker compose config`) nem imprima variáveis de ambiente, pois a saída pode revelar segredos.
- Após cada etapa relevante, execute verificações adequadas e relate com precisão o que foi implementado, testado, pendente de credenciais ou dependente de execução manual.
- Atualize o registro de execução em `PLANO_IMPLEMENTACAO.md` ao concluir cada fase. Nunca afirme que uma validação ocorreu se não foi executada.
- Não faça push sem autorização explícita. Preserve alterações do usuário e não use operações destrutivas sem autorização.
