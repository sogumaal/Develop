import ftplib
import os
import configparser
import re
from datetime import datetime
import tkinter as tk
from tkcalendar import Calendar
from tkinter import simpledialog


def seleccionar_fecha():
    def obtener_fecha():
        fecha_seleccionada = calendario.selection_get()
        ventana.destroy()
        fecha_str.set(fecha_seleccionada.strftime("%Y-%m-%d"))

    ventana = tk.Tk()
    ventana.title("Seleccionar fecha de respaldo")
    ventana.geometry("300x250")
    fecha_str = tk.StringVar()

    calendario = Calendar(ventana, selectmode='day', date_pattern='yyyy-mm-dd')
    calendario.pack(pady=20)

    boton = tk.Button(ventana, text="Confirmar", command=obtener_fecha)
    boton.pack()

    ventana.mainloop()
    return fecha_str.get()


def leer_guia():
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')

        ftp_host = config['ftp']['host']
        ftp_port = int(config['ftp']['port'])
        ftp_user = config['ftp']['user']
        ftp_pass = config['ftp']['password']
        ruta_remota = config['ftp']['ruta_remota_semanal']
        ruta_base_local = config['directorio']['ruta_local_semanal']

        # Mostrar calendario para seleccionar fecha
        fecha_input = seleccionar_fecha()
        fecha_objetivo = datetime.strptime(fecha_input.strip(), "%Y-%m-%d")
        fecha_str = fecha_objetivo.strftime("%Y%m%d")

        ruta_local = os.path.join(ruta_base_local, fecha_str)
        os.makedirs(ruta_local, exist_ok=True)

        print(f"Variables del proceso rescatadas. Archivos se guardarán en: {ruta_local}")
        return ftp_host, ftp_port, ftp_user, ftp_pass, ruta_remota, ruta_local, fecha_str
    except Exception as e:
        raise ValueError(f"Error al procesar el archivo de configuración: {e}")


def descargar_ftp(ftp_host, ftp_port, ftp_user, ftp_pass, ruta_remota, ruta_local, fecha_str):
    try:
        ftp = ftplib.FTP()
        ftp.connect(ftp_host, ftp_port)
        ftp.login(ftp_user, ftp_pass)

        def descargar_recursivamente(ruta_remota_actual):
            try:
                ftp.cwd(ruta_remota_actual)
                archivos = []
                ftp.retrlines('NLST', archivos.append)

                for archivo in archivos:
                    ruta_remota_archivo = os.path.join(ruta_remota_actual, archivo).replace("\\", "/")
                    ruta_local_archivo = os.path.join(ruta_local, archivo)

                    try:
                        ftp.cwd(ruta_remota_archivo)
                        ftp.cwd(ruta_remota_actual)
                        descargar_recursivamente(ruta_remota_archivo)
                    except ftplib.error_perm:
                        if fecha_str in archivo and archivo.endswith('.bak'):
                            if os.path.exists(ruta_local_archivo):
                                try:
                                    tamano_local = os.path.getsize(ruta_local_archivo)
                                    ftp.sendcmd("TYPE i")
                                    tamano_remoto = ftp.size(ruta_remota_archivo)
                                    if tamano_local == tamano_remoto:
                                        print(f"Archivo ya existe con mismo tamaño: {ruta_local_archivo}")
                                        continue
                                except Exception as e:
                                    print(f"Error al comparar tamaños: {e}")

                            with open(ruta_local_archivo, 'wb') as archivo_local:
                                ftp.retrbinary('RETR ' + archivo, archivo_local.write)
                            print(f"Descargado: {ruta_remota_archivo} → {ruta_local_archivo}")

            except Exception as e:
                print(f"Error en {ruta_remota_actual}: {e}")

        descargar_recursivamente(ruta_remota)
        ftp.quit()
        print("*************     Descarga completada.  *************")
        messagebox.showinfo("Finalizado", "**** Descarga completada. *******")

    except Exception as e:
        print(f"Error general: {e}")


if __name__ == "__main__":
    try:
        ftp_host, ftp_port, ftp_user, ftp_pass, ruta_remota, ruta_local, fecha_str = leer_guia()
        descargar_ftp(ftp_host, ftp_port, ftp_user, ftp_pass, ruta_remota, ruta_local, fecha_str)
        print("Proceso concluido.")
    except Exception as e:
        print(f"Error: {e}")
