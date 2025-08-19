import json
from django.http import JsonResponse
from django.db import connections
from django.views.decorators.csrf import csrf_exempt

def get(request):
    return JsonResponse({'message': 'Django is running!'})

def get_projects(request):
    if request.method == 'GET':
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT DISTINCT project_id, project_name, owner_email FROM projects_table;")
            rows = cursor.fetchall()

        # Convert to list of dicts
        return JsonResponse({'projects': [{'id': row[0], 'name': row[1], 'email': row[2]} for row in rows]})
    else:
        return JsonResponse({'error': 'GET request only'}, status=405)
    
def get_all_projects(request):
    if request.method == 'GET':
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT * FROM projects_table ORDER BY id ASC;")
            rows = cursor.fetchall()

        # Convert to list of dicts
        return JsonResponse({'projects': [
            {
                'id': row[1],
                'owner': row[2],
                'email': row[3],
                'name': row[4],
                'description': row[5],
                'role': row[6],
                'dateCreated': row[7],
            } for row in rows]})
    else:
        return JsonResponse({'error': 'GET request only'}, status=405)

@csrf_exempt
def get_project_details(request):
    if request.method == 'POST':
        try:
            # Parse JSON body
            body = json.loads(request.body.decode('utf-8'))
            email = body.get('email')
            project_id = body.get('project_id')

            if not email or not project_id:
                return JsonResponse({'error': 'Email and project_id are required'}, status=400)

            formatted_email = email.replace('@', '_').replace('.', '_')
            summary_table = f'summaries_{formatted_email.lower()}'
            conversations_table = f'conversations_{formatted_email.lower()}'
            summaries = []
            conversations = []

            with connections['default'].cursor() as cursor:
                # Function to check if a table exists in the database
                def table_exists(table_name):
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM information_schema.tables 
                        WHERE table_name = %s;
                    """, [table_name])
                    return cursor.fetchone()[0] == 1

                # Check and query summaries table
                if table_exists(summary_table):
                    summary_query = f"SELECT * FROM {summary_table} WHERE project_id = %s;"
                    cursor.execute(summary_query, [project_id])
                    summaries = cursor.fetchall()

                # Check and query conversations table
                if table_exists(conversations_table):
                    conversations_query = f"SELECT * FROM {conversations_table} WHERE project_id = %s;"
                    cursor.execute(conversations_query, [project_id])
                    conversations = cursor.fetchall()

            # If both are empty, project does not exist
            if not summaries and not conversations:
                return JsonResponse({'error': 'No project found for given filters'}, status=404)

            # Format conversation records if they exist
            conversation_data = [
                {
                    'role': row[2],
                    'content': row[3],
                    'created_at': row[4],
                } for row in conversations
            ] if conversations else None

            return JsonResponse({
                'summary': summaries[0][5] if summaries else None,
                'conversations': conversation_data,
            }, safe=False)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'POST request only'}, status=405)

def get_owners(request):
    if request.method == 'GET':
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT DISTINCT owner_email AS total_owners FROM projects_table;")
            rows = cursor.fetchall()

        return JsonResponse({'owners': [item[0] for item in rows]})
    else:
        return JsonResponse({'error': 'GET request only'}, status=405)
    
def get_summary_users(request):
    if request.method == 'GET':
        summaries = {}
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE 'summaries\_%' ESCAPE '\\';
            """)
            rows = cursor.fetchall()
            tables = [item[0] for item in rows]

            for table_name in tables:
                try:
                    query = f'SELECT project_id, status, project_name, created_at, role, file_source, commit_id FROM public."{table_name}" ORDER BY project_name ASC;'
                    cursor.execute(query)
                    rows = cursor.fetchall()

                    # Flatten and store in dict
                    summaries[table_name] = [
                        {
                            'project_id': row[0],
                            'status': row[1],
                            'project_name': row[2],
                            'created_at': row[3],
                            'role': row[4],
                            'file_source': row[5],
                            'commit_id': row[6]
                        } for row in rows
                    ]
                except Exception as e:
                    print(f"Error querying {table_name}: {e}")
                    summaries[table_name] = []

        return JsonResponse(summaries)
    else:
        return JsonResponse({'error': 'GET request only'}, status=405)

def get_conversation_users(request):
    if request.method == 'GET':
        summaries = {}
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE 'conversations\_%' ESCAPE '\\';
            """)
            rows = cursor.fetchall()
            tables = [item[0] for item in rows]

            for table_name in tables:
                try:
                    query = f'SELECT * FROM public."{table_name}";'
                    cursor.execute(query)
                    rows = cursor.fetchall()

                    # Flatten and store in dict
                    summaries[table_name] = [
                        {
                            'project_id': row[1],
                            'role': row[2],
                            'content': row[3],
                            'created_at': row[4],
                        } for row in rows
                    ]
                except Exception as e:
                    print(f"Error querying {table_name}: {e}")
                    summaries[table_name] = []

        return JsonResponse(summaries)
    else:
        return JsonResponse({'error': 'GET request only'}, status=405)
    
def get_pins_users(request):
    if request.method == 'GET':
        summaries = {}
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name LIKE 'pins\_%' ESCAPE '\\';
            """)
            rows = cursor.fetchall()
            tables = [item[0] for item in rows]

            for table_name in tables:
                try:
                    query = f'SELECT project_id, COUNT(*) AS total_rows FROM public.{table_name} GROUP BY project_id;'
                    cursor.execute(query)
                    project_ids = cursor.fetchall()
                    results = [{'project_id': row[0], 'count': row[1]} for row in project_ids]

                    # Flatten and store in dict
                    summaries[table_name] = results
                except Exception as e:
                    print(f"Error querying {table_name}: {e}")
                    summaries[table_name] = []

        return JsonResponse(summaries)
    else:
        return JsonResponse({'error': 'GET request only'}, status=405)

def get_checklist_assistant_threads(request):
    if request.method == 'GET':
        with connections['default'].cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT project_id, thread_id
                FROM public.assistants_table
                WHERE assistant_name = 'CHECKLIST_ASSISTANT';
            """)
            rows = cursor.fetchall()

        # Format as list of dictionaries
        results = [{'project_id': row[0], 'thread_id': row[1]} for row in rows]
        return JsonResponse({'checklist_assistant_threads': results})
    else:
        return JsonResponse({'error': 'GET request only'}, status=405)
    
