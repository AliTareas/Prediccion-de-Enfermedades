import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from lxml import etree
from PIL import Image, ImageTk
import os
import uuid

class PMMLPredictorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SISTEMAS EXPERTOS _ PEDRO CHÁVEZ")
        self.root.geometry("500x600")
        self.root.configure(bg="#f0f2f5")
        self.pmml_file = None
        self.data_fields = []
        self.inputs = {}
        self.tree_model = None

        
        try:
            self.root.iconphoto(True, ImageTk.PhotoImage(Image.open("lens_icon.png")))
        except Exception:
            pass 

        
        try:
            self.load_icon = ImageTk.PhotoImage(Image.open("load_icon.png").resize((20, 20)))
            self.predict_icon = ImageTk.PhotoImage(Image.open("predict_icon.png").resize((20, 20)))
        except Exception:
            self.load_icon = None
            self.predict_icon = None

        self.create_widgets()

    def create_widgets(self):
        
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 12), padding=10)
        style.configure("TLabel", font=("Helvetica", 12), background="#f0f2f5")
        style.configure("TCombobox", font=("Helvetica", 11))

        # Header
        header_frame = tk.Frame(self.root, bg="#0078d7", pady=10)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="SISTEMAS EXPERTOS _ PEDRO CHÁVEZ", font=("Helvetica", 16, "bold"), 
                 bg="#0078d7", fg="white").pack()

        # File selection
        file_frame = tk.Frame(self.root, bg="#f0f2f5", pady=10)
        file_frame.pack(fill="x", padx=20)
        tk.Button(file_frame, text="Cargar Archivo PMML", command=self.load_pmml, 
                  bg="#0078d7", fg="white", font=("Helvetica", 12), 
                  image=self.load_icon, compound="left").pack(fill="x")

        # Status label for loaded file
        self.status_label = tk.Label(self.root, text="Ningún archivo PMML cargado", 
                                    bg="#f0f2f5", font=("Helvetica", 10, "italic"))
        self.status_label.pack(pady=5)

        # Input frame with scrollbar
        canvas = tk.Canvas(self.root, bg="#f0f2f5")
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.input_frame = tk.Frame(canvas, bg="#f0f2f5")
        self.input_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.input_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=20)
        scrollbar.pack(side="right", fill="y")

        # Predict button
        tk.Button(self.root, text="Predecir", command=self.predict, 
                  bg="#28a745", fg="white", font=("Helvetica", 12), 
                  image=self.predict_icon, compound="left").pack(pady=20)

        # Result label
        self.result_label = tk.Label(self.root, text="", wraplength=400, 
                                    bg="#f0f2f5", font=("Helvetica", 12, "bold"))
        self.result_label.pack(pady=10)

    def load_pmml(self):
        file_path = filedialog.askopenfilename(filetypes=[("Archivos PMML", "*.pmml"), ("Todos los archivos", "*.*")])
        if not file_path:
            return
        self.pmml_file = file_path
        self.status_label.config(text=f"Archivo cargado: {os.path.basename(file_path)}")
        self.parse_pmml()
        self.create_input_fields()

    def parse_pmml(self):
        try:
            tree = etree.parse(self.pmml_file)
            ns = {"pmml": "http://www.dmg.org/PMML-4_2"}
            self.data_fields = []
            for data_field in tree.xpath("//pmml:DataDictionary/pmml:DataField", namespaces=ns):
                name = data_field.get("name")
                optype = data_field.get("optype")
                data_type = data_field.get("dataType")
                values = []
                if optype == "categorical":
                    values = [v.get("value") for v in data_field.xpath("pmml:Value", namespaces=ns)]
                elif optype == "continuous":
                    interval = data_field.xpath("pmml:Interval", namespaces=ns)
                    if interval:
                        left = float(interval[0].get("leftMargin"))
                        right = float(interval[0].get("rightMargin"))
                        values = (left, right)
                self.data_fields.append({"name": name, "optype": optype, "dataType": data_type, "values": values})
            self.tree_model = tree.xpath("//pmml:TreeModel", namespaces=ns)[0]
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo PMML: {str(e)}")
            self.pmml_file = None
            self.data_fields = []

    def create_input_fields(self):
        for widget in self.input_frame.winfo_children():
            widget.destroy()
        self.inputs = {}

        for field in self.data_fields:
            if field["name"] == "LENTE": 
                continue
            tk.Label(self.input_frame, text=field["name"].capitalize(), 
                     bg="#f0f2f5", font=("Helvetica", 11, "bold")).pack(anchor="w", pady=5)
            if field["optype"] == "categorical":
                var = tk.StringVar()
                combobox = ttk.Combobox(self.input_frame, textvariable=var, values=field["values"], state="readonly")
                combobox.pack(fill="x", pady=5)
                self.inputs[field["name"]] = var
            elif field["optype"] == "continuous":
                entry = tk.Entry(self.input_frame, font=("Helvetica", 11))
                entry.pack(fill="x", pady=5)
                self.inputs[field["name"]] = entry
                tk.Label(self.input_frame, text=f"Rango: {field['values'][0]} a {field['values'][1]}", 
                         bg="#f0f2f5", font=("Helvetica", 10)).pack(anchor="w")

    def predict(self):
        if not self.pmml_file or not self.tree_model:
            messagebox.showerror("Error", "Por favor, carga un archivo PMML válido primero.")
            return

        input_data = {}
        try:
            for field in self.data_fields:
                name = field["name"]
                if name == "LENTE":
                    continue
                value = self.inputs[name].get()
                if field["optype"] == "continuous":
                    value = float(value)
                    min_val, max_val = field["values"]
                    if not (min_val <= value <= max_val):
                        messagebox.showerror("Error", f"{name} debe estar entre {min_val} y {max_val}.")
                        return
                elif field["optype"] == "categorical" and value not in field["values"]:
                    messagebox.showerror("Error", f"Valor inválido para {name}. Selecciona de {field['values']}.")
                    return
                input_data[name] = value
        except ValueError:
            messagebox.showerror("Error", "Ingresa valores numéricos válidos para los campos continuos.")
            return

        ns = {"pmml": "http://www.dmg.org/PMML-4_2"}
        current_node = self.tree_model.xpath("//pmml:Node[pmml:True]", namespaces=ns)[0]
        while True:
            score = current_node.get("score")
            children = current_node.xpath("pmml:Node", namespaces=ns)
            if not children:
                break
            matched = False
            for child in children:
                predicate = child.xpath("pmml:SimplePredicate", namespaces=ns)
                if predicate:
                    field = predicate[0].get("field")
                    operator = predicate[0].get("operator")
                    value = predicate[0].get("value")
                    input_value = input_data.get(field)
                    if self.evaluate_predicate(input_value, operator, value, field in ["ASTIGMATISMO"]):
                        current_node = child
                        matched = True
                        break
            if not matched:
                break

        self.result_label.config(text=f"Predicción: {score or 'Sin predicción'}")

    def evaluate_predicate(self, input_value, operator, value, is_numeric):
        if is_numeric:
            input_value = float(input_value)
            value = float(value)
            if operator == "lessOrEqual":
                return input_value <= value
            elif operator == "greaterThan":
                return input_value > value
        else:
            return input_value == value
        return False

if __name__ == "__main__":
    root = tk.Tk()
    app = PMMLPredictorApp(root)
    root.mainloop()