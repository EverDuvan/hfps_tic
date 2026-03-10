import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hfps_tic.settings')
django.setup()

from inventory.models import CostCenter, Area

html_content = """<option value="101001 GERENCIA">101001 GERENCIA</option>
                        <option value="101002 SUBGERENCIA CIENTIFICA">101002 SUBGERENCIA CIENTIFICA</option>
                        <option value="101003 SUBGERENCIA ADMINISTRATIVA">101003 SUBGERENCIA ADMINISTRATIVA</option>
                        <option value="102002 CONTROL INTERNO">102002 CONTROL INTERNO</option>
                        <option value="108001 PLANEACIÓN">108001 PLANEACIÓN</option>
                        <option value="108005 SISTEMA OBLIGATORIO DE GARANTIA DE LA CALIDAD">108005 SISTEMA OBLIGATORIO
                            DE GARANTIA DE LA CALIDAD</option>
                        <option value="106006 GESTION JURIDICA">106006 GESTION JURIDICA</option>
                        <option value="105005 GESTION DE LA TECNOLOGIA">105005 GESTION DE LA TECNOLOGIA</option>
                        <option value="105001 GESTION DE INFORMACIÓN Y ESTADISTICA">105001 GESTION DE INFORMACIÓN Y
                            ESTADISTICA</option>
                        <option value="104003 SISTEMA DE GESTION SEGURIDAD Y SALUD EN EL TRABAJO">104003 SISTEMA DE
                            GESTION SEGURIDAD Y SALUD EN EL TRABAJO</option>
                        <option value="104001 ADMINISTRACIÓN DEL TALENTO HUMANO">104001 ADMINISTRACIÓN DEL TALENTO
                            HUMANO</option>
                        <option value="103001 COSTOS">103001 COSTOS</option>
                        <option value="103002 PRESUPUESTO">103002 PRESUPUESTO</option>
                        <option value="103003 CONTABILIDAD">103003 CONTABILIDAD</option>
                        <option value="103004 TESORERIA">103004 TESORERIA</option>
                        <option value="103006 FACTURACION">103006 FACTURACION</option>
                        <option value="103007 CARTERA">103007 CARTERA</option>
                        <option value="103008 GLOSAS">103008 GLOSAS</option>
                        <option value="106007 COMPRAS">106007 COMPRAS</option>
                        <option value="103009 CONTRATACIÓN Y VENTA DE SERVICIOS">103009 CONTRATACIÓN Y VENTA DE
                            SERVICIOS</option>
                        <option value="106001 ALMACEN Y ACTIVOS FIJOS">106001 ALMACEN Y ACTIVOS FIJOS</option>
                        <option value="105006 ADMINISTRACION DOCUMENTAL">105006 ADMINISTRACION DOCUMENTAL</option>
                        <option value="105008 COMUNICACIONES Y RELACIONAMIENTO">105008 COMUNICACIONES Y RELACIONAMIENTO
                        </option>
                        <option value="201013 VIGILANCIA EPIDEMIOLOGICA">201013 VIGILANCIA EPIDEMIOLOGICA</option>
                        <option value="201014 SEGURIDAD DEL PACIENTE">201014 SEGURIDAD DEL PACIENTE</option>
                        <option value="201012 AUDITORIA DE CALIDAD Y CONCURRENCIA">201012 AUDITORIA DE CALIDAD Y
                            CONCURRENCIA</option>
                        <option value="201009 REFERENCIA Y CONTRAREFERENCIA">201009 REFERENCIA Y CONTRAREFERENCIA
                        </option>
                        <option value="201011 SISTEMA DE ATENCION AL CIUDADANO">201011 SISTEMA DE ATENCION AL CIUDADANO
                        </option>
                        <option value="301005 URGENCIAS CONSULTAS Y PROCEDIMIENTOS">301005 URGENCIAS CONSULTAS Y
                            PROCEDIMIENTOS</option>
                        <option value="301006 URGENCIAS OBSERVACION">301006 URGENCIAS OBSERVACION</option>
                        <option value="305001 QUIROFANOS">305001 QUIROFANOS</option>
                        <option value="306002 SALA DE GINECOBSTETRICIA">306002 SALA DE GINECOBSTETRICIA</option>
                        <option value="304002 HOSPITALIZACION SALA GENERAL">304002 HOSPITALIZACION SALA GENERAL</option>
                        <option value="304005 HOSPITALIZACION SALA GENERAL PISO 1">304005 HOSPITALIZACION SALA GENERAL
                            PISO 1</option>
                        <option value="304004 HOSPITALIZACION PEDIATRIA">304004 HOSPITALIZACION PEDIATRIA</option>
                        <option value="201007 CENTRAL DE ESTERILIZACIÓN">201007 CENTRAL DE ESTERILIZACIÓN</option>
                        <option value="312001 SERVICIO FARMACEUTICO">312001 SERVICIO FARMACEUTICO</option>
                        <option value="307001 LABORATORIO CLINICO">307001 LABORATORIO CLINICO</option>
                        <option value="308001 RAYOS X">308001 RAYOS X</option>
                        <option value="310003 ECOGRAFIAS">310003 ECOGRAFIAS</option>
                        <option value="302001 CONSULTA EXTERNA GENERAL Y ENFERMERIA">302001 CONSULTA EXTERNA GENERAL Y
                            ENFERMERIA</option>
                        <option value="303001 CONSULTA EXTERNA ESPECIALIZADA">303001 CONSULTA EXTERNA ESPECIALIZADA
                        </option>
                        <option value="309001 TERAPIA RESPIRATORIA">309001 TERAPIA RESPIRATORIA</option>
                        <option value="309002 TERAPIA FISICA">309002 TERAPIA FISICA</option>
                        <option value="309007 TERAPIA OCUPACIONAL">309007 TERAPIA OCUPACIONAL</option>
                        <option value="309005 FONOAUDIOLOGIA">309005 FONOAUDIOLOGIA</option>
                        <option value="309006 PSICOLOGIA">309006 PSICOLOGIA</option>
                        <option value="309004 NUTRICION Y DIETETICA">309004 NUTRICION Y DIETETICA</option>
                        <option value="313002 ATENCIÓN AL PACIENTE CONSUMIDOR SPA">313002 ATENCIÓN AL PACIENTE
                            CONSUMIDOR SPA</option>
                        <option value="311001 AMBULANCIAS">311001 AMBULANCIAS</option>
                        <option value="106004 TRANSPORTE">106004 TRANSPORTE</option>
                        <option value="106002 MANTENIMIENTO">106002 MANTENIMIENTO</option>
                        <option value="106003 GESTION AMBIENTAL">106003 GESTION AMBIENTAL</option>
                        <option value="108006 PROYECTOS">108006 PROYECTOS</option>
                        <option value="104002 SEDE RECREATIVA">104002 SEDE RECREATIVA</option>"""

# Using regex to extract code and name.
opts = re.findall(r'<option[^>]*>([^<]+)</option>', html_content)

def run():
    print(f"Extracted {len(opts)} options.")
    for text in opts:
        text = text.strip().replace('\n', ' ')
        text = ' '.join(text.split())
        
        parts = text.split(' ', 1)
        if len(parts) == 2:
            code = parts[0]
            name = parts[1]
            
            # Create Cost Center
            cc, cc_created = CostCenter.objects.get_or_create(
                code=code,
                defaults={'name': name}
            )
            
            # Create Area
            area, area_created = Area.objects.get_or_create(
                name=name,
                defaults={'cost_center': cc}
            )
            
            # If area already existed, update its cost center to be safe
            if not area_created and not area.cost_center:
                area.cost_center = cc
                area.save()
            
            print(f"Processed: {code} - {name}")

if __name__ == '__main__':
    run()
