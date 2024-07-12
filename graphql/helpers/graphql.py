# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from graphql import parse, execute, GraphQLSchema, GraphQLObjectType, GraphQLField, GraphQLString, GraphQLInt, GraphQLList, GraphQLNonNull, GraphQLInputObjectType, GraphQLArgument
import psycopg2

# Fonction pour établir une connexion à la base de données PostgreSQL
def connect_db():
    conn = psycopg2.connect(
        dbname='your_dbname',
        user='your_user',
        password='your_password',
        host='your_host',
        port='your_port'
    )
    return conn

# Fonction pour exécuter une requête SQL
def execute_sql_query(query, variables):
    conn = None
    result = None
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute(query, variables)
        result = cur.fetchall()
        cur.close()
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return result

# Fonction pour générer dynamiquement les champs GraphQL en fonction des colonnes de la table
def generate_fields_for_table(table_name):
    query = f"""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = %s
    """
    columns = execute_sql_query(query, (table_name,))
    fields = {}
    for column in columns:
        column_name, data_type = column
        if data_type in ['integer', 'bigint']:
            fields[column_name] = GraphQLField(GraphQLInt)
        elif data_type in ['character varying', 'text']:
            fields[column_name] = GraphQLField(GraphQLString)
        # Ajoutez d'autres types de données selon les besoins
    return fields

# Fonction de résolution pour récupérer les données de la table
def resolve_table_data(table_name):
    def resolver(_, info):
        field_names = [field.name.value for field in info.field_nodes[0].selection_set.selections]
        fields = ", ".join(field_names)
        query = f"SELECT {fields} FROM {table_name}"
        data = execute_sql_query(query, ())
        return [
            {field_names[i]: row[i] for i in range(len(field_names))}
            for row in data
        ]
    return resolver

# Fonction pour générer dynamiquement le schéma GraphQL pour une table donnée
def generate_schema_for_table(table_name):
    fields = generate_fields_for_table(table_name)
    table_type = GraphQLObjectType(
        name=table_name.capitalize(),
        fields=fields
    )
    query_type = GraphQLObjectType(
        name='Query',
        fields={
            table_name: GraphQLField(
                GraphQLList(table_type),
                resolve=resolve_table_data(table_name)
            )
        }
    )
    
    # Générer les entrées pour les mutations
    input_fields = {}
    for name, field in fields.items():
        input_fields[name] = GraphQLField(field.type)
    
    input_type = GraphQLInputObjectType(
        name=f'{table_name.capitalize()}Input',
        fields=input_fields
    )
    
    def resolve_insert(_, info, input):
        columns = ', '.join(input.keys())
        values = ', '.join([f'%({key})s' for key in input.keys()])
        query = f'INSERT INTO {table_name} ({columns}) VALUES ({values}) RETURNING *'
        result = execute_sql_query(query, input)
        return result[0] if result else None

    def resolve_update(_, info, id, input):
        set_clause = ', '.join([f'{key} = %({key})s' for key in input.keys()])
        query = f'UPDATE {table_name} SET {set_clause} WHERE id = %(id)s RETURNING *'
        input['id'] = id
        result = execute_sql_query(query, input)
        return result[0] if result else None

    def resolve_delete(_, info, id):
        query = f'DELETE FROM {table_name} WHERE id = %s RETURNING *'
        result = execute_sql_query(query, (id,))
        return result[0] if result else None

    mutation_type = GraphQLObjectType(
        name='Mutation',
        fields={
            f'create_{table_name}': GraphQLField(
                table_type,
                args={'input': GraphQLArgument(input_type)},
                resolve=resolve_insert
            ),
            f'update_{table_name}': GraphQLField(
                table_type,
                args={
                    'id': GraphQLArgument(GraphQLNonNull(GraphQLInt)),
                    'input': GraphQLArgument(input_type)
                },
                resolve=resolve_update
            ),
            f'delete_{table_name}': GraphQLField(
                table_type,
                args={'id': GraphQLArgument(GraphQLNonNull(GraphQLInt))},
                resolve=resolve_delete
            )
        }
    )
    
    schema = GraphQLSchema(query=query_type, mutation=mutation_type)
    return schema

# Fonction pour exécuter une requête GraphQL dynamique
def execute_graphql_query(query, table_name, variables=None):
    schema = generate_schema_for_table(table_name)
    parsed_query = parse(query)
    result = execute(schema, parsed_query, variable_values=variables)
    return result.data

@csrf_exempt
def graphql_view(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            query = body.get('query')
            variables = body.get('variables')
            table_name = body.get('table_name')  # Vous devez envoyer le nom de la table dans le corps de la requête
            
            result = execute_graphql_query(query, table_name, variables)
            return JsonResponse(result, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)