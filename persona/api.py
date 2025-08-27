from .models import Persona

def findById(id) :
    Persona.objects.get(id=id)