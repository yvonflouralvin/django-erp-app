from django.shortcuts import render
from django.http import JsonResponse
from .helpers.db_graph_query import GraphQL
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
# Create your views here.


@csrf_exempt
@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def graphQL(request, model):
    
    """
    """
    gql = GraphQL()
    body = json.loads(request.body) if request.body else None 
    if request.method == "GET": 
        data = {}
        data['table_name'] = model

        if request.GET.get("columns") != None :
            data['columns'] = json.loads(request.GET.get("columns"))

        if  request.GET.get("condition") != None and request.GET.get("params") != None :
            data['condition'] = request.GET.get("condition")
            data['params'] = json.loads(request.GET.get("params"))

        if request.GET.get("page_number") != None and  request.GET.get('page_size') != None :
            data['page_size'] = int(request.GET.get('page_size'))
            data['page_number'] = int(request.GET.get("page_number"))

        result, total_rows, total_pages = gql.select_from_table(data)
        return JsonResponse({ 
            "datas": result,
            "total_rows": total_rows, 
            "total_pages" : total_pages, 
        })
    elif request.method == "POST":
        data = body
        data['table_name'] = model
        result = gql.insert_into_table(data)
        return JsonResponse({  
            "datas": result
        })
    elif request.method == "PUT":
        data = body
        data['table_name'] = model
        result = gql.update_table(data)
        return JsonResponse({ 
            "datas": result
        })