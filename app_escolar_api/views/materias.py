from django.db.models import *
from django.db import transaction
from app_escolar_api.serializers import *
from app_escolar_api.models import *
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
import json
from django.shortcuts import get_object_or_404


class MateriasAll(generics.CreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        materias = Materias.objects.all().order_by("id")
        lista = MateriaSerializer(materias, many=True).data
        
        for materia in lista:
            if isinstance(materia, dict) and "dias_json" in materia:
                try:
                    if isinstance(materia["dias_json"], str):
                        materia["dias_json"] = json.loads(materia["dias_json"])
                except Exception:
                    materia["dias_json"] = []
        
        return Response(lista, 200)


class MateriasView(generics.CreateAPIView):
    def get_permissions(self):
        if self.request.method in ['GET', 'PUT', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return []  
    
    def get(self, request, *args, **kwargs):
        materia = get_object_or_404(Materias, id=request.GET.get("id"))
        materia_data = MateriaSerializer(materia, many=False).data
        
        if isinstance(materia_data, dict) and "dias_json" in materia_data:
            try:
                if isinstance(materia_data["dias_json"], str):
                    materia_data["dias_json"] = json.loads(materia_data["dias_json"])
            except Exception:
                materia_data["dias_json"] = []
        
        return Response(materia_data, 200)
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            # Validar que el NRC no exista
            nrc = request.data.get("nrc")
            if Materias.objects.filter(nrc=nrc).exists():
                return Response({"message": f"El NRC {nrc} ya está registrado"}, 400)
            
            maestro = None
            maestro_data = request.data.get("maestro")
            
            if maestro_data:
                maestro_id = maestro_data.get("id") if isinstance(maestro_data, dict) else maestro_data
                if maestro_id:
                    maestro = get_object_or_404(Maestros, id=maestro_id)
            
            dias_json = request.data.get("dias_json", [])
            if isinstance(dias_json, str):
                try:
                    dias_json = json.loads(dias_json)
                except:
                    dias_json = []
            
            materia = Materias.objects.create(
                nrc=request.data["nrc"],
                nombre=request.data["nombre"],
                seccion=request.data.get("seccion"),
                dias_json=json.dumps(dias_json) if isinstance(dias_json, list) else dias_json,
                horario_inicio=request.data.get("horario_inicio"),
                horario_fin=request.data.get("horario_fin"),
                salon=request.data.get("salon"),
                programa_educativo=request.data.get("programa_educativo"),
                maestro=maestro,
                creditos=request.data.get("creditos")
            )
            materia.save()
            return Response({
                "message": "Materia registrada exitosamente",
                "materia_created_id": materia.id}, 201)
        except Exception as e:
            return Response({"message": f"Error al crear la materia: {str(e)}"}, 400)
    
    @transaction.atomic
    def put(self, request, *args, **kwargs):
        permission_classes = (permissions.IsAuthenticated,)
        
        try:
            materia = get_object_or_404(Materias, id=request.data["id"])
            
            materia.nombre = request.data.get("nombre", materia.nombre)
            materia.seccion = request.data.get("seccion", materia.seccion)
            materia.salon = request.data.get("salon", materia.salon)
            materia.programa_educativo = request.data.get("programa_educativo", materia.programa_educativo)
            materia.creditos = request.data.get("creditos", materia.creditos)
            
           
            if "horario_inicio" in request.data:
                materia.horario_inicio = request.data["horario_inicio"]
            if "horario_fin" in request.data:
                materia.horario_fin = request.data["horario_fin"]
            
            if "dias_json" in request.data:
                dias_json = request.data["dias_json"]
                if isinstance(dias_json, str):
                    try:
                        dias_json = json.loads(dias_json)
                    except:
                        dias_json = []
                materia.dias_json = json.dumps(dias_json) if isinstance(dias_json, list) else dias_json
            
            if "maestro" in request.data:
                maestro_data = request.data["maestro"]
                if maestro_data:
                    maestro_id = maestro_data.get("id") if isinstance(maestro_data, dict) else maestro_data
                    if maestro_id:
                        maestro = get_object_or_404(Maestros, id=maestro_id)
                        materia.maestro = maestro
                else:
                    materia.maestro = None
            
            materia.save()
            
            return Response({
                "message": "Materia actualizada correctamente",
                "materia": MateriaSerializer(materia).data
            }, 200)
        except Exception as e:
            return Response({"message": f"Error al actualizar la materia: {str(e)}"}, 400)
    
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        materia = get_object_or_404(Materias, id=request.GET.get("id"))
        try:
            materia.delete()
            return Response({"details": "Materia eliminada"}, 200)
        except Exception as e:
            return Response({"details": f"Algo pasó al eliminar: {str(e)}"}, 400)

class TotalMaterias(generics.CreateAPIView):
    def get(self, request, *args, **kwargs):
        

        materias_qs = Materias.objects.filter(maestro__user__is_active=True)
        lista_materias = MateriaSerializer(materias_qs, many=True).data

       
        for dias_json in lista_materias:
            try:
                dias_json["dias_json"] = json.loads(dias_json["dias_json"])
            except Exception:
                dias_json["dias_json"] = [] 

        total_materias = materias_qs.count()
        
        return Response(
            {
                "total_materias": total_materias
            },
            status=200
        )


