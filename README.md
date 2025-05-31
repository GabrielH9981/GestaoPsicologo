# Sistema de Gestão de Pacientes e Relatórios

Este projeto foi desenvolvido para auxiliar no gerenciamento de pacientes e relatórios de consultas, com funcionalidade de cadastro de pacientes, criação de relatórios, visualização de dados financeiros (valores gerados por consultas) e painel financeiro mensal. A aplicação utiliza Flask e MySQL para o backend, com uma interface simples e funcional.

## Funcionalidades

- **Cadastro de Pacientes:** Armazena as informações pessoais do paciente, como nome, data de nascimento, telefone e valor da sessão.
- **Listagem de Pacientes:** Exibe uma lista de pacientes cadastrados com a possibilidade de buscar pelo nome.
- **Criação de Relatório:** Relaciona um relatório a um paciente, com título, data e conteúdo.
- **Visualização de Relatório:** Exibe os relatórios detalhados de cada paciente.
- **Painel Financeiro:** Exibe o total de pacientes, a quantidade de consultas realizadas no mês e o valor gerado por paciente, com a possibilidade de filtrar por mês e ano.

## Tecnologias Usadas

- **Flask** - Framework web para Python
- **MySQL** - Banco de dados relacional
- **Bootstrap** - Framework CSS para estilização da interface
- **Jinja2** - Template engine para renderização das páginas HTML

## Instalação

### Requisitos

- Python 3.x
- MySQL 8.x
- pip (gerenciador de pacotes Python)

### Passos para rodar o projeto

1. **Clone o repositório:**

    ```bash
    git clone https://github.com/seu-usuario/projeto-aline.git
    cd projeto-aline
    ```

2. **Instale as dependências:**

    Se você estiver usando um ambiente virtual (recomendado), crie e ative o ambiente:

    ```bash
    python -m venv venv
    source venv/bin/activate  # no Linux/Mac
    venv\Scripts\activate     # no Windows
    ```

    Depois, instale as dependências do projeto:

    ```bash
    pip install -r requirements.txt
    ```

3. **Configure o banco de dados:**

    - Crie o banco de dados no MySQL (se não o fez ainda):
    
      ```sql
      CREATE DATABASE nome_do_banco;
      ```

    - Execute o script para criar as tabelas do banco de dados:

      ```bash
      python criar_banco.py
      ```

    **Nota:** Certifique-se de que suas credenciais do MySQL estão corretas.

4. **Execute a aplicação Flask:**

    Após configurar o banco de dados, você pode rodar a aplicação com o comando:

    ```bash
    python app.py
    ```

    A aplicação estará disponível em `http://127.0.0.1:5000/`.
