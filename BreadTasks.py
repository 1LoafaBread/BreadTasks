from dataclasses import dataclass, asdict
from typing import List, Optional
from tkinter import messagebox
import customtkinter as ctk
import datetime
import shutil
import json
import os
import sys

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

@dataclass
class Task:
    id: int
    text: str
    completed: bool = False
    createdAt: Optional[str] = None
    category: str = "Uncategorized"
    lastModified: Optional[str] = None
    
    def __post_init__(self):
        currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        if self.createdAt is None:
            self.createdAt = currentTime
        if self.lastModified is None:
            self.lastModified = currentTime

class BreadTasks:
    APP_NAME = "BreadTasks"
    VERSION = "1.0.0"
    DEFAULT_FILE = "breadtasks_data.json"
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"{self.APP_NAME} v{self.VERSION}")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        try:
            self.root.iconbitmap(default=self._get_icon_path())
        except:
            pass
        
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        self.tasks: List[Task] = []
        self.categories: List[str] = ["All", "Uncategorized"]
        self.nextId = 1
        self.currentCategory = "Uncategorized"
        self.selectedCategoryForButtons = None
        
        self.colors = {
            'primary': "#EDE9E3",
            'secondary': "#FAF9F7",
            'accent': "#3E7BFA",
            'accentLight': "#A7C5FF",
            'success': "#6BCB77",
            'danger': "#FF6B6B",
            'warning': "#FFB562",
            'textPrimary': "#2C2C2C",
            'textSecondary': "#555555",
            'border': "#DAD7D2",
            'sidebar': "#243447",
            'sidebarText': "#F2F4F6",
            'categoryColors': [
                "#3E7BFA", "#6BCB77", "#FFB562", "#A98EDA",
                "#48CFCB", "#FF77A9", "#6F7FF7", "#C7A17A",
                "#6D83F2", "#8AC926", "#FF9F1C", "#8338EC"
            ]
        }
        
        self.createSidebar()
        self.createMainContent()
        
        self.loadData()
        self.bindShortcuts()
        self.bindEvents()
        
        self.updateStatistics()
    
    def _get_icon_path(self) -> Optional[str]:
        filePath = os.path.join(os.getenv("LOCALAPPDATA") or "", "BreadTasks", "icon.ico")
        if os.path.exists(filePath):
            return filePath
        else:
            return None
    
    def createSidebar(self):
        self.sidebar = ctk.CTkFrame(self.root, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        titleFrame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        titleFrame.pack(fill="x", padx=20, pady=(30, 20))
        
        ctk.CTkLabel(
            titleFrame,
            text="🍞 BreadTasks",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=self.colors['sidebarText']
        ).pack(anchor="w")
        
        buttonFrame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        buttonFrame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(
            buttonFrame,
            text="➕ New Task",
            command=self.openAddTaskDialog,
            fg_color=self.colors['accent'],
            hover_color=self.colors['accentLight'],
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=8
        ).pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(
            buttonFrame,
            text="📁 New Category",
            command=self.openAddCategoryDialog,
            fg_color="#9575CD",
            hover_color="#B39DDB",
            font=ctk.CTkFont(size=14),
            height=40,
            corner_radius=8
        ).pack(fill="x")
        
        categoriesHeader = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        categoriesHeader.pack(fill="x", padx=20, pady=(30, 10))
        
        ctk.CTkLabel(
            categoriesHeader,
            text="CATEGORIES",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['sidebarText']
        ).pack(side="left")
        
        self.categoriesContainer = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            height=300,
            scrollbar_button_color=self.colors['sidebarText'],
            scrollbar_button_hover_color=self.colors['accent']
        )
        self.categoriesContainer.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.categoriesContainer.grid_columnconfigure(0, weight=1)
        
        statsFrame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        statsFrame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            statsFrame,
            text="STATISTICS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['sidebarText']
        ).pack(anchor="w", pady=(0, 15))
        
        self.totalLabel = ctk.CTkLabel(
            statsFrame,
            text="Total Tasks: 0",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['sidebarText']
        )
        self.totalLabel.pack(anchor="w", pady=2)
        
        self.completedLabel = ctk.CTkLabel(
            statsFrame,
            text="Completed: 0 (0%)",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['sidebarText']
        )
        self.completedLabel.pack(anchor="w", pady=2)
        
        self.categoryStatsLabel = ctk.CTkLabel(
            statsFrame,
            text="Current Category: Uncategorized",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['sidebarText']
        )
        self.categoryStatsLabel.pack(anchor="w", pady=2)
        
        versionFrame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        versionFrame.pack(fill="x", padx=20, pady=(10, 20))
        
        ctk.CTkLabel(
            versionFrame,
            text=f"v{self.VERSION}",
            font=ctk.CTkFont(size=10),
            text_color="#7E8C9A"
        ).pack(side="right")
    
    def createMainContent(self):
        self.mainContainer = ctk.CTkFrame(self.root, fg_color=self.colors['primary'])
        self.mainContainer.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.mainContainer.grid_rowconfigure(1, weight=1)
        self.mainContainer.grid_columnconfigure(0, weight=1)
        
        headerFrame = ctk.CTkFrame(self.mainContainer, fg_color="transparent")
        headerFrame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        headerFrame.grid_columnconfigure(0, weight=1)
        
        self.categoryTitle = ctk.CTkLabel(
            headerFrame,
            text="Uncategorized Tasks",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.colors['textPrimary']
        )
        self.categoryTitle.grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        actionsFrame = ctk.CTkFrame(headerFrame, fg_color="transparent")
        actionsFrame.grid(row=1, column=0, sticky="ew")
        actionsFrame.grid_columnconfigure(0, weight=1)
        
        searchFrame = ctk.CTkFrame(actionsFrame, height=40, 
                                   fg_color=self.colors['secondary'],
                                   corner_radius=8)
        searchFrame.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        searchFrame.grid_columnconfigure(0, weight=1)
        
        self.searchVar = ctk.StringVar()
        self.searchVar.trace("w", lambda *args: self.displayTasks())
        
        self.searchEntry = ctk.CTkEntry(
            searchFrame,
            textvariable=self.searchVar,
            placeholder_text="🔍 Search tasks...",
            border_width=0,
            fg_color="transparent",
            font=ctk.CTkFont(size=13),
            text_color=self.colors['textPrimary']
        )
        self.searchEntry.grid(row=0, column=0, sticky="ew", padx=15)
        
        ctk.CTkButton(
            actionsFrame,
            text="🗑️ Clear Completed",
            command=self.clearCompleted,
            fg_color=self.colors['danger'],
            hover_color="#D32F2F",
            font=ctk.CTkFont(size=13),
            height=40,
            width=140,
            corner_radius=8
        ).grid(row=0, column=1, sticky="e", padx=(0, 10))
        
        ctk.CTkButton(
            actionsFrame,
            text="📤 Export",
            command=self.exportTasks,
            fg_color=self.colors['accent'],
            hover_color=self.colors['accentLight'],
            font=ctk.CTkFont(size=13),
            height=40,
            width=100,
            corner_radius=8
        ).grid(row=0, column=2, sticky="e", padx=(10, 0))
        
        self.tasksFrame = ctk.CTkScrollableFrame(
            self.mainContainer,
            fg_color=self.colors['primary'],
            scrollbar_button_color=self.colors['border'],
            scrollbar_button_hover_color=self.colors['accent']
        )
        self.tasksFrame.grid(row=1, column=0, sticky="nsew")
        self.tasksFrame.grid_columnconfigure(0, weight=1)
    
    def displayCategories(self):
        for widget in self.categoriesContainer.winfo_children():
            widget.destroy()
        
        rowIdx = 0
        
        for idx, category in enumerate(self.categories):
            categoryColor = self.colors['categoryColors'][idx % len(self.colors['categoryColors'])]
            
            if category == "All":
                categoryColor = "#7E8C9A"
            
            isSelected = category == self.currentCategory
            isShowingButtons = category == self.selectedCategoryForButtons
            
            categoryCard = ctk.CTkFrame(
                self.categoriesContainer,
                fg_color=categoryColor if isSelected else self.colors['primary'],
                corner_radius=8,
                border_width=1,
                border_color=categoryColor if isSelected else self.colors['border']
            )
            categoryCard.grid(row=rowIdx, column=0, sticky="ew", pady=2)
            categoryCard.grid_columnconfigure(0, weight=1)
            rowIdx += 1
            
            contentFrame = ctk.CTkFrame(categoryCard, fg_color="transparent")
            contentFrame.pack(fill="x", padx=15, pady=10)
            
            if category == "All":
                count = len(self.tasks)
                displayName = f"📁 {category}"
            else:
                count = sum(1 for task in self.tasks if task.category == category)
                displayName = f"📂 {category}"
            
            nameFrame = ctk.CTkFrame(contentFrame, fg_color="transparent")
            nameFrame.pack(side="left", fill="x", expand=True)
            
            def makeSelectFunc(cat):
                def func(e=None):
                    if self.selectedCategoryForButtons == cat:
                        self.selectedCategoryForButtons = None
                    else:
                        self.selectedCategoryForButtons = cat
                    self.selectCategory(cat)
                return func
            
            selectFunc = makeSelectFunc(category)
            
            nameLabel = ctk.CTkLabel(
                nameFrame,
                text=displayName,
                font=ctk.CTkFont(size=13, weight="bold" if isSelected else "normal"),
                text_color="#FFFFFF" if isSelected else "#333333",
                anchor="w",
                cursor="hand2"
            )
            nameLabel.pack(side="left", fill="x", expand=True)
            nameLabel.bind("<Button-1>", selectFunc)
            
            if count > 0:
                countBadge = ctk.CTkLabel(
                    nameFrame,
                    text=str(count),
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="#FFFFFF",
                    fg_color=categoryColor if isSelected else "#666666",
                    corner_radius=10,
                    width=25,
                    height=20
                )
                countBadge.pack(side="right", padx=(5, 0))
                countBadge.bind("<Button-1>", selectFunc)
            
            for widget in [categoryCard, contentFrame, nameFrame]:
                widget.bind("<Button-1>", selectFunc)
                widget.configure(cursor="hand2")
            
            if isShowingButtons and category not in ["All", "Uncategorized"]:
                buttonCard = ctk.CTkFrame(
                    self.categoriesContainer,
                    fg_color=self.colors['primary'],
                    corner_radius=5,
                    border_width=1,
                    border_color=self.colors['border']
                )
                buttonCard.grid(row=rowIdx, column=0, sticky="ew", pady=(0, 2), padx=10)
                buttonCard.grid_columnconfigure(0, weight=1)
                rowIdx += 1
                
                buttonContainer = ctk.CTkFrame(buttonCard, fg_color="transparent")
                buttonContainer.pack(fill="x", padx=10, pady=8)
                
                editBtn = ctk.CTkButton(
                    buttonContainer,
                    text="✏️ Edit",
                    width=80,
                    height=30,
                    font=ctk.CTkFont(size=12),
                    fg_color=self.colors['accent'],
                    hover_color=self.colors['accentLight'],
                    corner_radius=6,
                    command=lambda c=category: self.openEditCategoryDialog(c)
                )
                editBtn.pack(side="left", padx=(0, 10))
                
                if count == 0:
                    deleteBtn = ctk.CTkButton(
                        buttonContainer,
                        text="🗑️ Delete",
                        width=80,
                        height=30,
                        font=ctk.CTkFont(size=12),
                        fg_color=self.colors['danger'],
                        hover_color="#D32F2F",
                        corner_radius=6,
                        command=lambda c=category: self.deleteCategory(c)
                    )
                    deleteBtn.pack(side="left")
                else:
                    deleteBtn = ctk.CTkButton(
                        buttonContainer,
                        text=f"🗑️ ({count} tasks)",
                        width=100,
                        height=30,
                        font=ctk.CTkFont(size=11),
                        fg_color="#CCCCCC",
                        hover_color="#CCCCCC",
                        state="disabled",
                        corner_radius=6
                    )
                    deleteBtn.pack(side="left")
    
    def displayTasks(self):
        for widget in self.tasksFrame.winfo_children():
            widget.destroy()
        
        if self.currentCategory == "All":
            filteredTasks = self.tasks
            self.categoryTitle.configure(text="All Tasks")
        else:
            filteredTasks = [t for t in self.tasks if t.category == self.currentCategory]
            self.categoryTitle.configure(text=f"{self.currentCategory} Tasks")
        
        searchTerm = self.searchVar.get().lower()
        if searchTerm:
            filteredTasks = [t for t in filteredTasks if searchTerm in t.text.lower()]
        
        self.updateStatistics()
        
        if not filteredTasks:
            emptyFrame = ctk.CTkFrame(self.tasksFrame, fg_color="transparent")
            emptyFrame.grid(row=0, column=0, pady=100)
            
            if searchTerm:
                message = f"🔍 No tasks found for '{searchTerm}'"
            else:
                message = "📝 No tasks in this category"
            
            ctk.CTkLabel(
                emptyFrame,
                text=message,
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=self.colors['textSecondary']
            ).pack()
            
            if not searchTerm and self.currentCategory != "All":
                ctk.CTkButton(
                    emptyFrame,
                    text=f"➕ Add Task to {self.currentCategory}",
                    command=self.openAddTaskDialog,
                    fg_color=self.colors['accent'],
                    hover_color=self.colors['accentLight'],
                    font=ctk.CTkFont(size=14),
                    height=40,
                    corner_radius=8
                ).pack(pady=20)
            
            return
        
        for idx, task in enumerate(filteredTasks):
            frame = ctk.CTkFrame(self.tasksFrame, fg_color="transparent")
            frame.grid(row=idx, column=0, sticky="ew", pady=5)
            frame.grid_columnconfigure(0, weight=1)
            
            self.createTaskWidget(task, frame)
    
    def createTaskWidget(self, task: Task, parentFrame):
        bgColor = self.colors['secondary']
        if task.completed:
            bgColor = "#F1F8E9"
        
        taskCard = ctk.CTkFrame(
            parentFrame,
            fg_color=bgColor,
            corner_radius=10,
            border_width=1,
            border_color=self.colors['border']
        )
        taskCard.grid(row=0, column=0, sticky="ew", pady=5)
        taskCard.grid_columnconfigure(1, weight=1)
        
        checkboxFrame = ctk.CTkFrame(taskCard, fg_color="transparent")
        checkboxFrame.grid(row=0, column=0, padx=15, pady=15, sticky="n")
        
        checkbox = ctk.CTkCheckBox(
            checkboxFrame,
            text="",
            width=24,
            height=24,
            command=lambda t=task: self.toggleTask(t.id),
            variable=ctk.BooleanVar(value=task.completed)
        )
        checkbox.pack()
        
        contentFrame = ctk.CTkFrame(taskCard, fg_color="transparent")
        contentFrame.grid(row=0, column=1, sticky="ew", padx=(0, 15), pady=15)
        contentFrame.grid_columnconfigure(0, weight=1)
        
        taskText = ctk.CTkLabel(
            contentFrame,
            text=task.text,
            font=ctk.CTkFont(size=14, weight="bold" if not task.completed else "normal"),
            text_color=self.colors['textPrimary'] if not task.completed else "#888888",
            anchor="w",
            wraplength=600
        )
        taskText.grid(row=0, column=0, sticky="w")
        
        metaFrame = ctk.CTkFrame(contentFrame, fg_color="transparent")
        metaFrame.grid(row=1, column=0, sticky="w", pady=(10, 0))
        
        if task.category != "Uncategorized":
            catIndex = self.categories.index(task.category) if task.category in self.categories else 0
            catColor = self.colors['categoryColors'][catIndex % len(self.colors['categoryColors'])]
            
            categoryBadge = ctk.CTkButton(
                metaFrame,
                text=task.category,
                width=80,
                height=25,
                font=ctk.CTkFont(size=11),
                fg_color=catColor,
                hover_color=catColor,
                corner_radius=6,
                command=lambda t=task: self.changeTaskCategory(t)
            )
            categoryBadge.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            metaFrame,
            text=f"📅 {task.createdAt[:10] if task.createdAt else 'No date'}",
            font=ctk.CTkFont(size=11),
            text_color=self.colors['textSecondary']
        ).pack(side="left")
        
        actionsFrame = ctk.CTkFrame(taskCard, fg_color="transparent")
        actionsFrame.grid(row=0, column=2, padx=15, pady=15, sticky="e")
        
        editBtn = ctk.CTkButton(
            actionsFrame,
            text="✏️ Edit",
            width=70,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors['accent'],
            hover_color=self.colors['accentLight'],
            corner_radius=6,
            command=lambda t=task: self.openEditTaskDialog(t)
        )
        editBtn.pack(side="left", padx=(0, 5))
        
        deleteBtn = ctk.CTkButton(
            actionsFrame,
            text="🗑️ Delete",
            width=70,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors['danger'],
            hover_color="#D32F2F",
            corner_radius=6,
            command=lambda t=task: self.removeTask(t.id)
        )
        deleteBtn.pack(side="left")
    
    def updateStatistics(self):
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.completed)
        percentage = (completed / total * 100) if total > 0 else 0
        
        self.totalLabel.configure(text=f"Total Tasks: {total}")
        self.completedLabel.configure(text=f"Completed: {completed} ({percentage:.1f}%)")
        
        if self.currentCategory == "All":
            catTotal = total
            catCompleted = completed
        else:
            catTasks = [t for t in self.tasks if t.category == self.currentCategory]
            catTotal = len(catTasks)
            catCompleted = sum(1 for t in catTasks if t.completed)
        
        self.categoryStatsLabel.configure(
            text=f"Current Category: {self.currentCategory} ({catCompleted}/{catTotal} completed)"
        )
    
    def selectCategory(self, category: str):
        self.currentCategory = category
        self.displayCategories()
        self.displayTasks()
    
    def openAddTaskDialog(self):
        dialog = self._create_dialog("Add New Task", 500, 350)
        
        ctk.CTkLabel(
            dialog,
            text="Add New Task",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(30, 20))
        
        taskEntry = ctk.CTkEntry(
            dialog,
            placeholder_text="Enter task description...",
            width=400,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        taskEntry.pack(pady=10)
        taskEntry.focus()
        
        categoryFrame = ctk.CTkFrame(dialog, fg_color="transparent")
        categoryFrame.pack(pady=20)
        
        ctk.CTkLabel(
            categoryFrame,
            text="Category:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(0, 10))
        
        defaultCategory = self.currentCategory if self.currentCategory != "All" else "Uncategorized"
        categoryVar = ctk.StringVar(value=defaultCategory)
        
        categoryDropdown = ctk.CTkComboBox(
            categoryFrame,
            values=[c for c in self.categories if c != "All"],
            variable=categoryVar,
            width=150,
            font=ctk.CTkFont(size=13),
            state="readonly"
        )
        categoryDropdown.pack(side="left")
        
        def addTaskFromDialog():
            text = taskEntry.get().strip()
            if not text:
                messagebox.showwarning("Warning", "Task description cannot be empty!")
                return
            
            task = Task(
                id=self.nextId, 
                text=text, 
                category=categoryVar.get()
            )
            self.tasks.append(task)
            self.nextId += 1
            
            self.displayTasks()
            self.displayCategories()
            self.saveData()
            dialog.destroy()
        
        buttonFrame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttonFrame.pack(pady=30)
        
        ctk.CTkButton(
            buttonFrame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            height=35,
            font=ctk.CTkFont(size=13),
            corner_radius=8
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            buttonFrame,
            text="Add Task",
            command=addTaskFromDialog,
            fg_color=self.colors['accent'],
            hover_color=self.colors['accentLight'],
            width=100,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8
        ).pack(side="left", padx=10)
        
        dialog.bind("<Return>", lambda e: addTaskFromDialog())
    
    def openEditTaskDialog(self, task: Task):
        dialog = self._create_dialog("Edit Task", 500, 350)
        
        ctk.CTkLabel(
            dialog,
            text="Edit Task",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(30, 20))
        
        taskEntry = ctk.CTkEntry(
            dialog,
            placeholder_text="Enter task description...",
            width=400,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        taskEntry.pack(pady=10)
        taskEntry.insert(0, task.text)
        taskEntry.focus()
        
        categoryFrame = ctk.CTkFrame(dialog, fg_color="transparent")
        categoryFrame.pack(pady=20)
        
        ctk.CTkLabel(
            categoryFrame,
            text="Category:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(0, 10))
        
        categoryVar = ctk.StringVar(value=task.category)
        
        categoryDropdown = ctk.CTkComboBox(
            categoryFrame,
            values=[c for c in self.categories if c != "All"],
            variable=categoryVar,
            width=150,
            font=ctk.CTkFont(size=13),
            state="readonly"
        )
        categoryDropdown.pack(side="left")
        
        def saveEditedTask():
            text = taskEntry.get().strip()
            if not text:
                messagebox.showwarning("Warning", "Task description cannot be empty!")
                return
            
            for t in self.tasks:
                if t.id == task.id:
                    t.text = text
                    t.category = categoryVar.get()
                    t.lastModified = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    break
            
            self.displayTasks()
            self.displayCategories()
            self.saveData()
            dialog.destroy()
        
        buttonFrame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttonFrame.pack(pady=30)
        
        ctk.CTkButton(
            buttonFrame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            height=35,
            font=ctk.CTkFont(size=13),
            corner_radius=8
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            buttonFrame,
            text="Save Changes",
            command=saveEditedTask,
            fg_color=self.colors['success'],
            hover_color="#388E3C",
            width=120,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8
        ).pack(side="left", padx=10)
        
        dialog.bind("<Return>", lambda e: saveEditedTask())
    
    def openAddCategoryDialog(self):
        dialog = self._create_dialog("Add New Category", 400, 200)
        
        ctk.CTkLabel(
            dialog,
            text="Add New Category",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(30, 20))
        
        categoryEntry = ctk.CTkEntry(
            dialog,
            placeholder_text="Enter category name...",
            width=300,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        categoryEntry.pack(pady=10)
        categoryEntry.focus()
        
        def addCategoryFromDialog():
            categoryName = categoryEntry.get().strip()
            if not categoryName:
                messagebox.showwarning("Warning", "Category name cannot be empty!")
                return
            
            if categoryName in self.categories:
                messagebox.showwarning("Warning", "Category already exists!")
                return
            
            self.categories.append(categoryName)
            self.displayCategories()
            self.saveData()
            dialog.destroy()
        
        buttonFrame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttonFrame.pack(pady=20)
        
        ctk.CTkButton(
            buttonFrame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            height=35,
            font=ctk.CTkFont(size=13),
            corner_radius=8
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            buttonFrame,
            text="Add Category",
            command=addCategoryFromDialog,
            fg_color="#9575CD",
            hover_color="#B39DDB",
            width=120,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8
        ).pack(side="left", padx=10)
        
        dialog.bind("<Return>", lambda e: addCategoryFromDialog())
    
    def openEditCategoryDialog(self, categoryName: str):
        self.selectedCategoryForButtons = None
        
        dialog = self._create_dialog("Edit Category", 400, 200)
        
        ctk.CTkLabel(
            dialog,
            text="Edit Category",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(30, 20))
        
        categoryEntry = ctk.CTkEntry(
            dialog,
            placeholder_text="Enter new category name...",
            width=300,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        categoryEntry.pack(pady=10)
        categoryEntry.insert(0, categoryName)
        categoryEntry.focus()
        
        def saveCategoryChanges():
            newName = categoryEntry.get().strip()
            if not newName:
                messagebox.showwarning("Warning", "Category name cannot be empty!")
                return
            
            if newName in self.categories and newName != categoryName:
                messagebox.showwarning("Warning", "Category already exists!")
                return
            
            index = self.categories.index(categoryName)
            self.categories[index] = newName
            
            for task in self.tasks:
                if task.category == categoryName:
                    task.category = newName
            
            if self.currentCategory == categoryName:
                self.currentCategory = newName
            
            self.displayCategories()
            self.displayTasks()
            self.saveData()
            dialog.destroy()
        
        buttonFrame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttonFrame.pack(pady=20)
        
        ctk.CTkButton(
            buttonFrame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            height=35,
            font=ctk.CTkFont(size=13),
            corner_radius=8
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            buttonFrame,
            text="Save Changes",
            command=saveCategoryChanges,
            fg_color="#9575CD",
            hover_color="#B39DDB",
            width=120,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8
        ).pack(side="left", padx=10)
        
        dialog.bind("<Return>", lambda e: saveCategoryChanges())
    
    def changeTaskCategory(self, task: Task):
        dialog = self._create_dialog("Move Task", 400, 200)
        
        ctk.CTkLabel(
            dialog,
            text="Move Task to Another Category",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(30, 20))
        
        ctk.CTkLabel(
            dialog,
            text=f"Task: {task.text[:50]}{'...' if len(task.text) > 50 else ''}",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['textSecondary']
        ).pack()
        
        categoryFrame = ctk.CTkFrame(dialog, fg_color="transparent")
        categoryFrame.pack(pady=20)
        
        ctk.CTkLabel(
            categoryFrame,
            text="New Category:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(0, 10))
        
        categoryVar = ctk.StringVar(value=task.category)
        
        categoryDropdown = ctk.CTkComboBox(
            categoryFrame,
            values=[c for c in self.categories if c != "All"],
            variable=categoryVar,
            width=150,
            font=ctk.CTkFont(size=13),
            state="readonly"
        )
        categoryDropdown.pack(side="left")
        
        def moveTask():
            newCategory = categoryVar.get()
            if task.category == newCategory:
                dialog.destroy()
                return
            
            task.category = newCategory
            task.lastModified = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            self.displayTasks()
            self.displayCategories()
            self.saveData()
            dialog.destroy()
        
        buttonFrame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttonFrame.pack(pady=20)
        
        ctk.CTkButton(
            buttonFrame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            height=35,
            font=ctk.CTkFont(size=13),
            corner_radius=8
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            buttonFrame,
            text="Move Task",
            command=moveTask,
            fg_color=self.colors['accent'],
            hover_color=self.colors['accentLight'],
            width=100,
            height=35,
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8
        ).pack(side="left", padx=10)
        
        dialog.bind("<Return>", lambda e: moveTask())
    
    def deleteCategory(self, categoryName: str):
        self.selectedCategoryForButtons = None
        
        if categoryName in ["All", "Uncategorized"]:
            messagebox.showwarning("Warning", "Cannot delete this category!")
            return
        
        taskCount = sum(1 for task in self.tasks if task.category == categoryName)
        
        if taskCount > 0:
            response = messagebox.askyesno(
                "Category Not Empty",
                f"Category '{categoryName}' has {taskCount} task(s).\n"
                f"All tasks will be moved to 'Uncategorized'.\n"
                f"Do you want to continue?"
            )
            
            if response:
                for task in self.tasks:
                    if task.category == categoryName:
                        task.category = "Uncategorized"
                        task.lastModified = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        else:
            response = messagebox.askyesno(
                "Delete Category",
                f"Are you sure you want to delete category '{categoryName}'?"
            )
        
        if response:
            self.categories.remove(categoryName)
            
            if self.currentCategory == categoryName:
                self.currentCategory = "Uncategorized"
            
            self.displayCategories()
            self.displayTasks()
            self.saveData()
    
    def removeTask(self, taskId: int):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this task?"):
            self.tasks = [task for task in self.tasks if task.id != taskId]
            self.displayTasks()
            self.displayCategories()
            self.saveData()
    
    def toggleTask(self, taskId: int):
        for task in self.tasks:
            if task.id == taskId:
                task.completed = not task.completed
                task.lastModified = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                break
        self.displayTasks()
        self.saveData()
    
    def clearCompleted(self):
        if self.currentCategory == "All":
            tasksToClear = [t for t in self.tasks if t.completed]
        else:
            tasksToClear = [t for t in self.tasks if t.completed and t.category == self.currentCategory]
        
        if not tasksToClear:
            messagebox.showinfo("Info", "No completed tasks to clear!")
            return
        
        if messagebox.askyesno(
            "Clear Completed", 
            f"Are you sure you want to clear {len(tasksToClear)} completed task(s) "
            f"from '{self.currentCategory}'?"
        ):
            self.tasks = [t for t in self.tasks if t not in tasksToClear]
            self.displayTasks()
            self.displayCategories()
            self.saveData()
    
    def exportTasks(self):
        try:
            from tkinter import filedialog
            
            filePath = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile="breadtasks_export.json"
            )
            
            if filePath:
                exportData = {
                    'exportDate': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'appVersion': self.VERSION,
                    'tasks': [asdict(task) for task in self.tasks],
                    'categories': self.categories,
                    'statistics': {
                        'totalTasks': len(self.tasks),
                        'completedTasks': sum(1 for t in self.tasks if t.completed),
                        'categoriesCount': len([c for c in self.categories if c not in ["All", "Uncategorized"]])
                    }
                }
                
                with open(filePath, 'w', encoding='utf-8') as f:
                    json.dump(exportData, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Export Successful", 
                                  f"Tasks exported successfully to:\n{filePath}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export tasks: {str(e)}")
    
    def get_data_path(self) -> str:
        filePath = os.path.join(os.getenv("LOCALAPPDATA") or "", "BreadTasks", self.DEFAULT_FILE)
        return filePath
    
    def saveData(self):
        try:
            tasksData = []
            for task in self.tasks:
                taskDict = asdict(task)
                tasksData.append(taskDict)
            
            data = {
                'version': self.VERSION,
                'lastSaved': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'tasks': tasksData,
                'categories': self.categories,
                'nextId': self.nextId,
                'currentCategory': self.currentCategory
            }
            
            filePath = self.get_data_path()
            with open(filePath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass
    
    def loadData(self):
        try:
            filePath = self.get_data_path()
            
            if os.path.exists(filePath):
                with open(filePath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.tasks = []
                
                for taskDict in data.get('tasks', []):
                    if 'priority' in taskDict:
                        taskDict.pop('priority')
                    if 'category' not in taskDict:
                        taskDict['category'] = "Uncategorized"
                    if 'lastModified' not in taskDict:
                        taskDict['lastModified'] = taskDict.get('createdAt')
                    
                    task = Task(**taskDict)
                    self.tasks.append(task)
                
                self.categories = data.get('categories', ["All", "Uncategorized"])
                
                if "All" not in self.categories:
                    self.categories.insert(0, "All")
                if "Uncategorized" not in self.categories:
                    self.categories.append("Uncategorized")
                
                self.nextId = data.get('nextId', len(self.tasks) + 1)
                self.currentCategory = data.get('currentCategory', "Uncategorized")
                
                seen = set()
                self.categories = [cat for cat in self.categories if not (cat in seen or seen.add(cat))]
                
            else:
                self.createDefaultDataFile()
            
            self.displayCategories()
            self.displayTasks()
            
        except json.JSONDecodeError:
            self.createDefaultDataFile()
            self.displayCategories()
            self.displayTasks()
            
        except Exception as e:
            self.createDefaultDataFile()
            self.displayCategories()
            self.displayTasks()
    
    def createDefaultDataFile(self):
        try:
            defaultData = {
                'version': self.VERSION,
                'lastSaved': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'tasks': [],
                'categories': ["All", "Uncategorized"],
                'nextId': 1,
                'currentCategory': "Uncategorized"
            }
            
            filePath = self.get_data_path()
            with open(filePath, 'w', encoding='utf-8') as f:
                json.dump(defaultData, f, indent=2, ensure_ascii=False)
            
            self.tasks = []
            self.categories = ["All", "Uncategorized"]
            self.nextId = 1
            self.currentCategory = "Uncategorized"
            
        except Exception as e:
            pass
    
    def _create_dialog(self, title: str, width: int, height: int) -> ctk.CTkToplevel:
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry(f"{width}x{height}")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        return dialog
    
    def bindShortcuts(self):
        self.root.bind('<Control-n>', lambda e: self.openAddTaskDialog())
        self.root.bind('<Delete>', lambda e: self.clearCompleted())
        self.root.bind('<Control-f>', lambda e: self.searchEntry.focus())
        self.root.bind('<Control-c>', lambda e: self.openAddCategoryDialog())
        self.root.bind('<Escape>', lambda e: self.searchVar.set(""))
        self.root.bind('<Control-e>', lambda e: self.exportTasks())
    
    def bindEvents(self):
        self.root.protocol("WM_DELETE_WINDOW", self.onClosing)
    
    def onClosing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit BreadTasks?"):
            self.saveData()
            self.root.destroy()
            sys.exit(0)

def main():
    targetDir = os.path.join(os.getenv("LOCALAPPDATA") or "", "BreadTasks")
    os.makedirs(targetDir, exist_ok=True)

    basePath = getattr(sys, "_MEIPASS", "")
    sourceFile = os.path.join(basePath, "icon.ico") if basePath else os.path.join(".", "icon.ico")
    targetFile = os.path.join(targetDir, "icon.ico")

    if not os.path.exists(targetFile):
        shutil.copy2(sourceFile, targetFile)

    root = ctk.CTk()
    app = BreadTasks(root)

    root.update_idletasks()
    width = 1200
    height = 800
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    root.mainloop()

if __name__ == "__main__":
    main()