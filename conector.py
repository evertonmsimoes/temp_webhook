import pymysql
import time
from send_webhook import send_info_n8n

# Configurações de conexão com o banco 
db_settings = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'db': 'suitecrm',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
}

# Dicionário para armazenar o último ID e a última data de modificação da última consulta
last_data = {}
# Dicionário para armazenar os IDs registrados no banco e realizar a verificação do método (Insert/Update)
data_db = {}

def obter_ids_da_tabela(table_name):
    connection = pymysql.connect(**db_settings)
    try:
        with connection.cursor() as cursor:
            # Execute uma consulta SELECT para obter todos os IDs da tabela
            query = f"SELECT id FROM {table_name}"
            cursor.execute(query)
            # Obtenha todos os resultados como uma lista de dicionários
            results = cursor.fetchall()
            # Extraia os IDs da lista de resultados
            ids = [result['id'] for result in results]
            return ids
    finally:
        connection.close()

# Função para obter e passar para o WebHook as informações da última alteração em uma tabela
def print_last_change(table_name):
    connection = pymysql.connect(**db_settings)
    try:
        with connection.cursor() as cursor:
            query = f"SELECT * FROM {table_name} WHERE date_modified > %(last_update)s ORDER BY date_modified DESC LIMIT 1"
            cursor.execute(query, {'last_update': last_update})
            result = cursor.fetchone()
            if result:
                last_entry = last_data.get(table_name)
                if last_entry is None or result['id'] != last_entry['id'] or result['date_modified'] != last_entry['date_modified']:

                    #  Busca as PrimaryKey se a chave com o nome da tabela não for encontrada no dicionario.
                    if table_name not in data_db:
                        data_db[table_name] = obter_ids_da_tabela(table_name)

                    if result['id'] not in data_db[table_name]:
                        headers = {
                            'Content-Type': 'application/json',
                            'X-Operation-Type': 'Insert',
                            'X-Table-Name': table_name,
                        }
                        data_db[table_name].append(result['id'])
                    else:
                        headers = {
                            'Content-Type': 'application/json',
                            'X-Operation-Type': 'Update',
                            'X-Table-Name': table_name,
                        }

                    # Adicionar a chave 'email' ao dicionário result para a tabela 'contacts'
                    if table_name == 'contacts':
                        email_query = f"""
                            SELECT ea.email_address 
                            FROM email_addresses ea
                            JOIN email_addr_bean_rel eabr ON ea.id = eabr.email_address_id
                            WHERE eabr.bean_module = 'Contacts' AND eabr.bean_id = %(bean_id)s
                            ORDER BY eabr.date_created DESC
                            LIMIT 1
                        """
                        cursor.execute(email_query, {'bean_id': result['id']})
                        email_result = cursor.fetchone()
                        if email_result:
                            result['email'] = email_result['email_address']

                    send_info_n8n(result, headers)
                    # Adicione colunas para verificação sobre alteração e inserção no banco
                    last_data[table_name] = {'id': result['id'], 'date_modified': result['date_modified']}
    finally:
        connection.close()

# Obtendo o timestamp do momento da última alteração nas tabelas
last_update = time.strftime('%Y-%m-%d %H:%M:%S')

# Exibindo informações da última alteração nas tabelas
for table_name in ['accounts', 'opportunities', 'contacts']:
    print_last_change(table_name)
    data_db[table_name] = obter_ids_da_tabela(table_name)

# Monitorando alterações nas tabelas
while True:
    time.sleep(5)  # Aguarda 5 segundos antes de verificar novamente
    for table_name in ['accounts', 'opportunities', 'contacts']:
        print_last_change(table_name)
