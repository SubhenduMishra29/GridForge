# GridForge V2 — Operator's Manual

**Document status:** Working manual, first edition  
**Audience:** First-time users, electrical engineers, technicians and project operators  
**Repository baseline:** `SubhenduMishra29/GridForge`, branch `main` as inspected on 6 November 2026  
**Purpose:** Explain how to operate GridForge without requiring programming knowledge.

> **Important:** This is an operational guide, not a declaration that every engineering feature is complete or commissioned. The manual distinguishes functions visible in the current source from functions that still require end-to-end UI verification. Do not use an unsupported or unverified study result for equipment procurement, protection setting approval, switching instructions or plant operation.

---

## How to use this manual

Read Chapters 1–5 before creating your first project. Then follow the practical workflows in the order shown.

Each procedure uses the following format:

- **Goal** — what you are trying to accomplish.
- **Before you begin** — information to collect.
- **Steps** — actions to perform.
- **Check your work** — how to confirm the result.
- **If something goes wrong** — safe recovery guidance.

Names of buttons and panels are written exactly where they have been confirmed in the current application source. Where the visible menu wording or a workflow has not yet been verified in a running application, it is identified as **UI verification required** rather than guessed.

## Contents

1. [What GridForge does](#1-what-gridforge-does)
2. [Installation and first launch](#2-installation-and-first-launch)
3. [Understanding the application window](#3-understanding-the-application-window)
4. [Understanding projects and documents](#4-understanding-projects-and-documents)
5. [Create, save, open and close a project](#5-create-save-open-and-close-a-project)
6. [Understand the SLD canvas](#6-understand-the-sld-canvas)
7. [Add equipment using the Equipment Library](#7-add-equipment-using-the-equipment-library)
8. [Configure equipment in Properties](#8-configure-equipment-in-properties)
9. [Understand connections and the electrical network](#9-understand-connections-and-the-electrical-network)
10. [Select and inspect equipment](#10-select-and-inspect-equipment)
11. [Understand validation and messages](#11-understand-validation-and-messages)
12. [Studies and engineering results](#12-studies-and-engineering-results)
13. [Protection, control and dynamics](#13-protection-control-and-dynamics)
14. [Save safely and recover from problems](#14-save-safely-and-recover-from-problems)
15. [Electrical safety and engineering responsibility](#15-electrical-safety-and-engineering-responsibility)
16. [Troubleshooting guide](#16-troubleshooting-guide)
17. [Glossary](#17-glossary)
18. [Known limitations and manual maintenance](#18-known-limitations-and-manual-maintenance)

---

# 1. What GridForge does

GridForge is a power-system engineering application. It is intended to help an engineer build an electrical network model, draw and manage its Single-Line Diagram (SLD), configure engineering equipment, and work with supported studies and engineering information.

A project may contain:

- Electrical equipment such as buses, breakers, lines, transformers, loads and sources.
- Equipment terminals and explicit electrical connections.
- One or more SLD documents and their drawing layout.
- Study cases and supported engineering configuration.
- Measurement, protection and control information where the corresponding workflow is implemented.

### 1.1 Three things that must not be confused

| Term | Meaning in everyday language |
|---|---|
| Equipment | The real electrical device being represented, such as a breaker or transformer. |
| Connection / network | The actual electrical relationship between equipment terminals. |
| SLD symbol | The drawing symbol used to show the equipment on the screen. |

A symbol is not the equipment itself. Moving a symbol on the drawing changes its presentation position; it does not automatically change the electrical network.

### 1.2 The basic working sequence

A normal engineering task follows this sequence:

1. Create or open a project.
2. Open the appropriate engineering workspace.
3. Add equipment to the project.
4. Enter the equipment's engineering data.
5. establish the required terminal connections.
6. Review validation messages.
7. Run only a study supported by the current application.
8. Review the result and its warnings.
9. Save the project.

Do not skip network validation simply because the drawing looks correct.

---

# 2. Installation and first launch

## 2.1 Computer requirements

The current repository package configuration specifies:

- Python **3.12** (Python 3.12.x; versions below 3.12 and 3.13 or later are outside the declared range).
- PySide6 6.7 or later, below 7.
- NumPy 2.x.
- SciPy 1.x.

A compatible Windows or Linux desktop environment is required for the graphical application. The application window has a minimum size of 1200 × 800 pixels; a larger display is recommended.

**Do not install Python 3.10 for this repository baseline.** The current `pyproject.toml` explicitly requires Python 3.12. If a packaged installer is later provided, its own release instructions will supersede these developer installation steps.

## 2.2 Windows installation from the source repository

These instructions are for an operator who has received or downloaded the GridForge source folder.

1. Install Python 3.12 from the official Python distribution.
2. During installation, enable the option to add Python to PATH.
3. Open the GridForge project folder in File Explorer.
4. Click the folder address bar, type `cmd`, and press Enter. A Command Prompt opens in that folder.
5. Create a private Python environment:

   ```powershell
   py -3.12 -m venv .venv
   ```

6. Activate it:

   ```powershell
   .venv\Scripts\activate
   ```

7. Update the package installer:

   ```powershell
   python -m pip install --upgrade pip
   ```

8. Install GridForge and its declared runtime dependencies:

   ```powershell
   python -m pip install -e .
   ```

9. Start GridForge:

   ```powershell
   python main.py
   ```

Keep the Command Prompt open while using this source-based installation. Closing the application window ends the graphical session; the terminal may show diagnostic information.

## 2.3 Linux installation from the source repository

From the GridForge repository folder:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python main.py
```

If the operating system reports missing Qt platform libraries or display components, resolve those system dependencies for your Linux distribution. Do not copy random DLL or shared-library files into the GridForge source tree.

## 2.4 First-launch check

When GridForge opens:

1. Wait for the startup process to finish.
2. Confirm that the main window appears and the startup splash reports that GridForge is ready.
3. Confirm that the engineering workspace is visible.
4. Check that the canvas and the available panels have loaded.
5. If the application exits or displays an error, retain the complete terminal error output for support.

**UI verification required:** This edition does not yet provide screenshots for every supported operating system, display scaling setting or first-run condition.

---

# 3. Understanding the application window

GridForge organizes work into engineering workspaces. A workspace is a coordinated arrangement of editors and panels for a particular activity.

The current application architecture defines these discipline workspaces:

- **SLD** — electrical single-line diagram authoring and inspection.
- **Control** — control-system engineering workspace.
- **Protection** — protection engineering workspace.
- **Study** — engineering study workspace.

The exact workspace-switching control and its visible label must be confirmed against the running UI before this manual assigns a click-by-click menu instruction.

## 3.1 Common screen areas

| Area | What it is for |
|---|---|
| Main application window | The outer GridForge window. |
| Engineering canvas/editor | The main working surface for the active discipline. |
| Equipment Library | Search and select available equipment types. |
| Project Explorer | Browse the project hierarchy and its engineering objects. |
| Properties | Inspect or configure the selected object or an active creation draft. |
| Messages / validation | Read application messages and validation feedback. |
| Study Cases | View the study-case presentation area. |
| Toolbar / tool shelf | Request an interaction tool such as Select, Bus or Wire. |
| Status area | Contextual application and editor status. |

Panel placement can change with workspace composition. A panel may be docked, moved, floated or hidden depending on the active layout. If a panel is not visible, first inspect the current workspace and panel visibility controls; do not assume that the underlying project data has been deleted.

## 3.2 Project Explorer

The Project Explorer presents a hierarchy of the active project. The current projection groups information under headings such as:

- Network Elements
- Documents
- Study Cases

Network elements are grouped by their equipment type. Selecting an element in the hierarchy is linked to the application's selection state and can be used to locate an object for inspection.

## 3.3 Equipment Library

The Equipment Library contains the available equipment catalogue.

- Use **Search components…** to filter the list.
- Equipment entries are grouped by category.
- Selecting an equipment entry requests the corresponding creation tool.
- The selected equipment type is not yet a committed network object merely because it has been selected in the library.

## 3.4 Properties panel

The Properties panel is contextual. It can show the parameters of a selected object or the details of a draft being prepared.

Two visible actions in the current implementation are:

- **Apply / Commit** — applies editable property changes or commits the applicable creation draft, depending on the current context.
- **Commit Network** — requests validation and commit of the current draft network. The action is enabled only when a draft network is available.

Do not press a commit action repeatedly while the first operation is still running. Wait for the completion message.

---

# 4. Understanding projects and documents

A **project** is the main container for an engineering job. It holds the canonical project and network state. An **SLD document** is a drawing/presentation document associated with the project.

A project and its SLD drawing are related, but they are not interchangeable:

- Equipment and electrical relationships belong to the engineering model.
- Drawing positions, routes and annotations belong to the presentation.
- A project can contain a collection of documents.
- Reopening a project restores its saved semantic state and rebuilds the graphical presentation.

## 4.1 Project file format

GridForge uses the `.gridforge` project package. The package contains:

```text
ProjectName.gridforge/
├── manifest.json
└── project.json
```

The manifest identifies package/schema/version information. The project file contains the saved project state. Treat the package as one project unit: do not edit, rename or delete internal JSON files manually.

---

# 5. Create, save, open and close a project

## 5.1 Create a new project

**Goal:** Start a separate engineering job.

**Before you begin:** Decide the project name and choose a folder where you have write permission and sufficient disk space.

1. Launch GridForge.
2. Use the application's project creation command. **UI verification required:** confirm the exact menu/button label in the running build.
3. Enter the project name and select the destination when prompted.
4. Confirm the creation request.
5. Wait for the project workspace and its initial SLD document to become active.
6. Check the Project Explorer for the new project root and its Documents section.
7. Save the project before entering substantial engineering data.

Use a clear project name, for example `WHRS_Auxiliary_Power_System`. Avoid names such as `New Project 1` or `Final Final`.

## 5.2 Save a project

1. Use the application's Save command.
2. If the project has not yet been assigned a location, use the Save As workflow and choose the destination.
3. Wait for the save operation to finish.
4. Confirm that no save error or failure message is displayed.
5. Keep a separate backup copy at meaningful milestones.

The project package is the authoritative saved file. Do not assume that a visible drawing change has been saved until the save operation has completed.

## 5.3 Open an existing project

1. Use the application's Open Project command. **UI verification required:** confirm the exact visible command label.
2. Browse to the required `.gridforge` package.
3. Select the package and confirm.
4. Wait for loading and project activation to finish.
5. Inspect the Project Explorer and active SLD.
6. Check the Messages/validation area for loading or restoration warnings.

If GridForge rejects the package, do not modify its internal files to force it open. Preserve the original and work on a backup copy.

## 5.4 Close or switch projects

When a project has unsaved changes, GridForge presents a decision with these options:

- **Save** — save changes before closing or switching.
- **Discard** — close or switch without retaining the unsaved changes.
- **Cancel** — stop the close/switch request and return to the current project.

Choose **Cancel** if you are uncertain. Choose **Discard** only when you are certain that the changes are not required.

---

# 6. Understand the SLD canvas

The Single-Line Diagram (SLD) is the graphical engineering workspace used to represent the electrical system.

The canvas is not a freehand drawing sheet. Equipment placement, connection creation and electrical network commitment are separate operations.

## 6.1 The three confirmed basic tools

The current toolbar implementation identifies these concrete tools:

| Tool | Identifier | Purpose |
|---|---|---|
| Select | `select` | Select and work with existing canvas objects. |
| Bus | `bus` | Start bus creation/placement. |
| Wire | `wire` | Start a connection-drawing interaction. |

The Equipment Library also selects equipment-specific creation tools from the catalogue.

## 6.2 Preview versus committed equipment

When you select an equipment type, GridForge activates a creation workflow. The object may appear as a draft or preview while you position it and enter its data.

A draft is not the same as a committed network object.

Follow the on-screen Properties instructions and validation messages. Where the current workflow exposes a **Commit Network** action, use it only after the intended equipment and connections have been prepared. Wait for the completion result.

## 6.3 Moving and arranging symbols

Moving or arranging an SLD symbol is a presentation operation. It does not, by itself:

- change the equipment's electrical parameters;
- create a terminal connection;
- close a breaker;
- establish a physical neutral or earth-return path; or
- prove that a network is electrically valid.

After significant editing, inspect the resulting equipment and network state rather than relying on the appearance of the drawing alone.

---

# 7. Add equipment using the Equipment Library

## 7.1 General procedure

1. Open the SLD workspace.
2. Locate the **Equipment Library** panel.
3. Click the **Search components…** field.
4. Type the equipment name or a category/type keyword.
5. Review the filtered catalogue entries.
6. Select the required equipment entry.
7. Confirm that the corresponding creation tool becomes active.
8. Follow the canvas placement and Properties workflow.
9. Enter the required engineering parameters.
10. Review validation feedback.
11. Commit the draft/network using the available commit action when the intended network is complete.

Selecting an entry in the library changes the active creation request. If another creation session is in progress, switching equipment may cancel that transient session. Finish or deliberately cancel the current draft before selecting a different type.

## 7.2 Equipment data checklist

Before committing an electrical object, collect the manufacturer's or approved design data that applies to that object.

Examples:

| Equipment | Typical information to prepare |
|---|---|
| Bus | Name/identifier, nominal voltage and applicable bus configuration. |
| Breaker | Rated voltage/current, interrupting duty, poles and operating state. |
| Transformer | Rated power, winding voltages, impedance, vector group, tap data and grounding details. |
| Line/Cable | Length, conductor data, impedance/resistance/reactance and applicable construction details. |
| Load | Active/reactive demand, voltage and operating assumptions. |
| Generator | Rated data and the fault/sequence/dynamic parameters required by the selected study. |
| Motor | Rated data and the model parameters required by the selected study. |
| CT/PT/CVT | Ratio, polarity, accuracy/class and the required primary/secondary terminal details. |

This table is a preparation checklist, not a claim that every listed parameter editor or study path is currently complete. Enter only fields actually provided by the current editor and supported by its validation contract. Do not substitute guessed values for missing nameplate or test data.

---

# 8. Configure equipment in Properties

## 8.1 Inspect a selected object

1. Select the object in the SLD or Project Explorer.
2. Open or locate the **Properties** panel.
3. Confirm that the displayed identity and equipment type match the intended object.
4. Review the displayed status and parameter fields.
5. Check any validation or availability message before editing.

The panel may display a message that a parameter is unavailable in the committed read model. This means the field is not currently available for editing through that view; it does not authorize an operator to invent or silently substitute a value.

## 8.2 Apply a change

1. Select the intended object.
2. Change only the fields that are editable.
3. Review units and engineering bases carefully.
4. Press **Apply / Commit** when enabled.
5. Read the result or validation message.
6. Re-select the object and confirm the saved value.
7. Save the project.

If a value is rejected, read the validation message and correct the input. Do not repeatedly submit the same invalid value.

## 8.3 Transformer configuration

A transformer may require winding-specific configuration in addition to general nameplate data. Confirm the HV/LV winding identity, connection, terminal roles, vector group, tap information and grounding data against the approved transformer documents.

The existence of a transformer configuration editor does not mean every transformer construction or every numerical study case is supported. Review the study's diagnostics and stated coverage before using results.

---

# 9. Understand connections and the electrical network

This is one of the most important chapters for a new operator.

## 9.1 What is a terminal?

A terminal is a physical electrical connection point belonging to a piece of equipment.

For example, a two-ended line has two physical ends. A breaker has two sides. A transformer has terminals associated with its windings.

A connection must identify the intended terminal endpoints. Drawing two symbols close together is not enough.

## 9.2 What is a bus?

A bus is an electrical connection point to which multiple compatible equipment terminals may be connected. It is not merely a thick line drawn on the canvas.

## 9.3 Simple Wire connection

The conventional Simple Wire relationship is a persistent terminal-to-terminal network relationship.

When drawing a connection:

1. Activate the Wire tool.
2. Identify the intended source equipment terminal.
3. Start the connection at that terminal.
4. Route the line toward the intended destination terminal.
5. Finish at the actual destination terminal.
6. Review the resulting connection and any validation feedback.
7. Commit the draft network when the workflow requires it.

The exact endpoint acquisition gestures and completion shortcut must be verified against the running build before a later edition documents mouse-button or keyboard instructions.

**Important:** A line crossing, visual overlap, nearby endpoint or route polyline does not automatically create an electrical junction. Confirm the actual connection identity in the application.

## 9.4 Breaker state and connectivity

A breaker is physical switching equipment. Its open/closed and in-service state affects the network's conductive topology.

Do not confuse:

- the breaker symbol's appearance;
- the breaker equipment state;
- the derived network connectivity; and
- the numerical model used by a study.

A drawing that shows a breaker between two buses does not prove that the breaker is closed or that a study treats it as in service.

## 9.5 Neutral and earth paths

Neutral and protective-earth paths are physical electrical paths, not decorative labels. A study that requires neutral/earth return must have the supported physical conductor construction and grounding information.

Do not assume that an earth symbol, a neutral label or a line drawn on the SLD creates a valid earth-return path.

---

# 10. Select and inspect equipment

1. Activate the Select tool.
2. Click the intended symbol, or select its entry in the Project Explorer.
3. Confirm the selected item is highlighted.
4. Read the Properties panel.
5. If the wrong item is selected, clear or replace the selection and try again.

When multiple objects overlap, use the Project Explorer to select by equipment name/type where possible.

A selection is an editing aid. It does not change the electrical state of the selected object.

---

# 11. Understand validation and messages

GridForge uses validation feedback to identify invalid, incomplete or unsupported engineering input.

When a message appears:

1. Read the entire message.
2. Identify the object or operation named in it.
3. Return to the relevant Properties or connection workflow.
4. Correct the underlying input if the cause is understood.
5. Retry the operation once.
6. Confirm that the message clears or that the operation reports success.

### Common message categories

| Message type | What it usually means | Operator response |
|---|---|---|
| Missing/invalid parameter | Required input is absent or outside an allowed range. | Check the equipment data and units. |
| Incompatible endpoint | The selected terminals cannot be connected under the current contract. | Check terminal identity and equipment type. |
| Draft validation | The uncommitted network contains an issue. | Correct the draft before committing. |
| Unsupported study case | The requested model/path is not implemented for this configuration. | Do not treat the result as valid; consult the study coverage. |
| Save/load error | The project could not be saved or restored completely. | Preserve the original package and report the message. |

A successful drawing operation is not the same as successful electrical validation. A successful project save is not the same as a verified numerical study.

---

# 12. Studies and engineering results

GridForge architecture includes study workflows such as power flow, short circuit, dynamics and protection studies. The availability and completeness of each operator-facing workflow must be verified against the specific application release.

Before running a study, prepare:

- a saved project;
- a reviewed equipment and connectivity model;
- the study configuration and operating assumptions;
- valid equipment parameters and bases;
- applicable source, grounding and switching data; and
- an understanding of the study's supported equipment/model coverage.

After a study completes:

1. Confirm that the study reports completion rather than failure or unsupported status.
2. Review all warnings and diagnostics.
3. Confirm the study case and project identity.
4. Review units, bases and sign conventions.
5. Check that the result belongs to the intended model revision.
6. Save or export results only through the supported result workflow.

Never use a numerical result without reviewing its assumptions, warnings, model coverage and provenance.

**UI verification required:** This edition does not yet prescribe click-by-click study execution or report export. Those procedures will be added after each study editor and its actual Application command path are inspected and demonstrated.

---

# 13. Protection, control and dynamics

These are separate engineering disciplines. Do not assume that configuring one automatically configures the others.

## 13.1 Protection

Protection engineering can involve instrument transformers, physical secondary wiring, measurement channels, relay inputs, protection functions, decisions, output mapping and switching-device operation.

A protection decision is not itself proof that a breaker has physically opened. The trip/action path and equipment feedback must be supported and verified.

Before relying on a protection result, verify the instrument ratio/polarity, secondary circuit, channel identity, input quality/freshness, relay function, settings, trip mapping and breaker target.

## 13.2 Control

Control engineering concerns logic, permissives, interlocks, timers, input/output signals and commands. A control indication is not proof of a physical output or field-device acknowledgement.

Use only control functions that are available and documented in the installed release.

## 13.3 Dynamics

Dynamic simulation represents time-dependent system behaviour. It may require a compatible operating point, dynamic equipment parameters and control models.

Do not treat a dynamic model as a replacement for the saved static electrical network.

---

# 14. Save safely and recover from problems

## 14.1 Recommended save discipline

Save at these milestones:

- immediately after creating the project;
- after adding a major group of equipment;
- after completing a network section;
- before changing transformer, source or protection configuration;
- after completing a validated study configuration; and
- before closing or switching projects.

Keep backups outside the active working package. Use dated, meaningful names for backup copies.

## 14.2 If the application becomes unresponsive

1. Wait briefly if a commit or study operation is visibly in progress.
2. Do not start a second commit.
3. If the application remains unresponsive, record the time and the last action.
4. Close only through normal application controls if possible.
5. Preserve the project package and any terminal error output.
6. Reopen a copy of the project first if recovery is uncertain.

## 14.3 If a project fails to open

- Keep the original package unchanged.
- Check that the selected item is a `.gridforge` package.
- Confirm that the file is not still being copied or synchronized.
- Try a backup copy.
- Record the complete error message and the application version.

Do not manually edit `manifest.json` or `project.json` to bypass validation.

---

# 15. Electrical safety and engineering responsibility

GridForge is an engineering software tool. It is not a substitute for approved plant procedures, equipment interlocks, protection coordination approval, statutory requirements or competent engineering judgement.

- Never use GridForge to issue live switching instructions unless a separately approved and commissioned operational integration explicitly provides that capability.
- Do not change real equipment settings solely on the basis of an unreviewed software result.
- Verify all input data against approved drawings, nameplates, test certificates and design documents.
- Check voltage, current, power, impedance bases, units and phase/sequence conventions.
- Treat unsupported or incomplete model coverage as a limitation, not as a zero value.
- Have critical calculations independently reviewed in accordance with the organization's engineering quality process.

---

# 16. Troubleshooting guide

| Problem | First checks |
|---|---|
| GridForge does not start | Confirm Python 3.12 is active, the virtual environment is activated and `python -m pip install -e .` completed. |
| `No module named PySide6` | Activate the environment and reinstall the declared project dependencies. |
| Equipment Library is empty | Check that the application finished startup and the Equipment Library panel is present. Capture the terminal error if it is not populated. |
| Selecting equipment cancels a draft | This can happen when changing to a different creation tool. Recreate the intended draft and complete one creation workflow at a time. |
| Apply / Commit is disabled | Select an object or draft and check whether any editable parameter is available. |
| Commit Network is disabled | The action is enabled only when a draft network is available. Check whether equipment or connections have actually been added to the draft. |
| A connection looks correct but is not electrically connected | Check the actual terminal endpoints and committed network relationship. Visual crossing or proximity is not proof of connectivity. |
| A study reports unsupported coverage | Do not bypass the diagnostic. Review the equipment model, required data and supported study scope. |
| Unsaved changes prompt appears | Choose Save, Discard or Cancel deliberately. Cancel preserves the current session. |
| Project fails to load | Preserve the original package and report the full diagnostic; test a backup copy. |

When reporting a problem, include the GridForge version/commit, operating system, Python version, project package (if it can be shared safely), exact steps, expected behaviour, actual behaviour and full error text. Remove confidential plant information before sharing.

---

# 17. Glossary

| Term | Plain-language explanation |
|---|---|
| Application | The controlled workflow layer that performs and validates engineering operations. |
| Bus | A common electrical connection point for multiple equipment terminals. |
| Canvas | The visible drawing/work surface of an editor. |
| Core | The authoritative engineering model and electrical-domain rules. |
| Draft | A temporary, not-yet-committed creation or network state. |
| Equipment | A represented physical electrical device. |
| Inspector / Properties | The panel used to inspect or edit selected equipment or a draft. |
| Network | The authoritative electrical relationships and derived connectivity. |
| Project | The main saved engineering job and its associated data. |
| SLD | Single-Line Diagram; a simplified graphical representation of an electrical system. |
| Study | A defined engineering calculation or simulation over a project model. |
| Terminal | A physical electrical connection point on equipment. |
| Topology | Which electrical points are connected under the applicable equipment and switching states. |
| Workspace | A coordinated arrangement of editors and panels for a discipline. |

---

# 18. Known limitations and manual maintenance

This is the first working edition. The following procedures require further source tracing and hands-on UI verification before they can be documented as fully operational click-by-click workflows:

- exact first-run project creation, Save As and Open dialog wording;
- exact workspace switching and panel visibility controls;
- mouse/keyboard gestures for equipment placement, wire endpoint acquisition and canvas navigation;
- complete equipment-specific parameter forms and validation behaviour;
- end-to-end power-flow and short-circuit execution, result inspection and export;
- end-to-end protection configuration, measurement wiring, trip mapping and feedback;
- control logic authoring and runtime operation;
- dynamic simulation setup and result review;
- backup/restore and recovery demonstrations.

A future manual revision should add screenshots captured from the actual running application, with numbered callouts that match the written steps. Screenshots must be refreshed whenever the corresponding UI workflow changes.

### Release update rule

For every manual update:

1. Inspect the current authoritative `main` branch.
2. Verify the described screen, panel, command and workflow in source and, where possible, in the running application.
3. Separate implemented behaviour from partial or planned behaviour.
4. Update the affected procedure and screenshots.
5. Record the manual revision date and the GridForge baseline used.
6. Do not claim that tests, CI, numerical verification or commissioning were performed unless they actually were.

**End of working first edition.**


---

# 19. Menu-by-menu reference

This chapter describes the menu structure defined in the current GridForge source. Menu contents can be disabled when an action is not available in the current project, workspace or selection context. A disabled command is not a fault by itself.

To use a menu, click its name on the menu bar, read the command label, and click the required command. A trailing ellipsis (…) means that the command normally opens a dialog or requests further information. Read the dialog before confirming.

## 19.1 File menu

The File menu contains project and application lifecycle commands.

| Menu command | Shortcut | Purpose and operating instruction |
|---|---|---|
| New Project | Ctrl+N | Start a new engineering project. Use when beginning a separate job. Save the previous project first. Enter the requested project details in the dialog and confirm. |
| Open Project… | Ctrl+O | Open an existing GridForge project package. Choose the intended `.gridforge` file. Do not select an unrelated JSON file from inside the package. |
| Save Project | Ctrl+S | Save the active project's current changes. Use frequently and before switching tasks. Wait for the save to complete. |
| Save Project As… | Ctrl+Shift+S | Save the current project to a new destination/name when the workflow supports it. Use this to create a separate working copy; verify which project is active afterward. |
| Close Project | Ctrl+W | Close the active project. Resolve any unsaved-changes prompt deliberately. Cancel if unsure. |
| Exit | Alt+F4 | Exit GridForge. The application first asks the project lifecycle boundary to approve closing. If a save/close decision is pending, resolve it before exiting. |

**Important:** New/Open/Save/Save As/Close are project operations. They are not the same as adding or removing an SLD symbol.

## 19.2 Edit menu

| Menu command | Shortcut | Purpose and operating instruction |
|---|---|---|
| Undo | Ctrl+Z | Reverse the last supported Application command. Inspect the result; undo is not guaranteed to reverse every presentation-only gesture. |
| Redo | Ctrl+Y | Reapply the last command that was undone. Use only after confirming that the redo is the intended change. |
| Delete Selection | Delete | Remove the selected object through the current editor's supported delete route. Check the selection before using it. |
| Select All | Ctrl+A | Select all objects covered by the active editor's selection scope. Confirm the active editor before using it. |
| Copy | Ctrl+C | Copy the selected SLD representation where the active editor supports copy. This is not a guarantee that every engineering object or connection is duplicated. |
| Paste | Ctrl+V | Paste the copied representation where supported. Inspect the new object's identity, properties and connections before relying on it. |
| Cut | Ctrl+X | Copy and remove the selected SLD representation where supported. Verify what was removed and whether the network object is affected. |

**Caution with Delete and Cut:** Before deleting, cutting or pasting electrical equipment, inspect the object identity and connected network. A visually selected symbol may be only a presentation object. Confirm the resulting engineering model after the operation.

## 19.3 View menu

| Menu command | Purpose and operating instruction |
|---|---|
| Maximize Editor (Ctrl+Space) | Give the active editor more screen area by minimizing surrounding presentation regions. Use when detailed drawing or inspection is required. Toggle back using the same command if the current implementation supports the reverse action. |
| Explorer | Show/hide the Explorer region for browsing project objects. Use it to locate an object by its project hierarchy rather than by clicking a crowded drawing. |
| Inspector | Show/hide the Inspector/Properties region. Use it to review the selected object's information. |
| Messages | Show/hide the Messages region. Open it when an operation reports a warning or rejection. |
| Tool Settings | Show/hide the tool settings region. This area is intended for settings belonging to the active tool; the exact available fields depend on the tool. |
| Fit SLD View | Fit the SLD drawing into the visible canvas. Use after zooming, panning or losing sight of the drawing. |
| Zoom In | Increase the displayed scale. This changes the view, not the electrical model. |
| Zoom Out | Decrease the displayed scale so more of the drawing is visible. |
| Pan | Activate view navigation so the canvas can be repositioned. Panning does not move electrical equipment in the project model. |
| Equipment Browser | Open/show the equipment catalogue. Search for a component, then select it to activate its creation workflow. |

## 19.4 SLD menu

| Menu command | Purpose and operating instruction |
|---|---|
| Select | Return to the selection/inspection interaction. Use before selecting existing objects or when you need to stop creating a new object. |
| Place Bus | Activate bus creation. Prepare the bus data, position it on the SLD and complete the creation workflow. A bus is an electrical node, not just a graphic line. |
| Wire | Activate terminal-to-terminal connection drawing. Start and finish at the intended equipment terminals; do not rely on visual crossing or proximity. |
| Commit Draft (Ctrl+Shift+Enter) | Request commitment of the current draft network. First inspect all equipment, parameters and endpoints. Wait for the result and read validation messages. |

## 19.5 Study menu

| Menu command | Purpose and operating instruction |
|---|---|
| Study Cases | Open the Study Cases panel/workflow. Use it to define a case, select its study type, enter study-specific data, run the case and inspect available results. |

The current Study Cases panel exposes Power Flow, Short-Circuit and Transient Stability as study-type choices. Actual execution depends on the Application's registered study capabilities and valid model data.

## 19.6 Reports menu

| Menu command | Purpose and operating instruction |
|---|---|
| Study Reports | Open the published study-results/report presentation. Use it to inspect results already produced by a supported study. Do not interpret an empty report area as a zero-valued engineering result. |

## 19.7 Window menu

| Menu command | Purpose and operating instruction |
|---|---|
| SLD | Activate the Single-Line Diagram workspace. This is the default initial workspace. |
| Control | Activate the Control engineering workspace for ladder/control logic and signal/action mapping. |
| Protection | Activate the Protection engineering workspace for relay, measurement and protection configuration/analysis. |
| Study | Activate the Study workspace for study preparation and result/report presentation. |
| Topology | Show the Application's topology projection. Use it to inspect the electrical connectivity view, not to edit drawing geometry. |
| Map | Show persisted SLD geometry/presentation information. It is a drawing/layout view, not a geographic map unless a separate feature explicitly says so. |

## 19.8 Help menu

| Menu command | Purpose and operating instruction |
|---|---|
| About GridForge | Display application identity/version information. Use this when reporting a problem so support can identify the build. |

---

# 20. Toolbar and SLD tool shelf reference

The toolbar is a fast-access row of commands. A tool button changes the active interaction; an action button performs an operation. Tool buttons may be shown as selected/pressed while active. Hover over a button to read its tooltip where available.

## 20.1 Primary SLD tools

### Select

**Purpose:** Select and inspect existing SLD objects.

**How to use:**
1. Click Select.
2. Click the object you want to inspect.
3. Confirm that the intended object is highlighted.
4. Read its details in Properties/Inspector.
5. To stop an active creation tool, return to Select.

**Use it when:** You need to inspect, select or edit an existing object rather than create a new one.

**Common mistake:** Clicking a symbol while another tool is active may start a creation or connection operation instead of selecting it.

### Bus

**Purpose:** Start creation of a bus.

**How to use:**
1. Click Bus or SLD → Place Bus.
2. Move to the intended canvas position.
3. Follow the preview and Properties instructions.
4. Enter the bus identity and engineering information requested by the editor.
5. Complete placement and commit the network when required.
6. Verify the bus in Project Explorer and the topology projection.

**Check:** Confirm that the bus is a project/network object and that intended equipment terminals are connected to it.

### Wire

**Purpose:** Create a terminal-to-terminal electrical connection.

**How to use:**
1. Click Wire or SLD → Wire.
2. Identify the correct starting terminal.
3. Start the connection on that terminal.
4. Route the connection to the intended destination.
5. Finish on the destination terminal.
6. Read the feedback and inspect the resulting network relationship.
7. Commit the draft network when required.

**Check:** The connection must be present in the electrical network, not merely visible as a line.

## 20.2 SLD editing and view toolbar actions

| Toolbar action | What it does | How/when to use |
|---|---|---|
| Box Select | Select objects inside a rectangular selection region. | Use when selecting several objects in a crowded area. Check the selected set before moving or deleting. |
| Move | Move selected SLD objects through the Select tool. | Select the intended object(s), invoke Move and follow the active editor interaction. This changes drawing placement, not electrical connectivity. |
| Drag Move | Drag selected SLD objects. | Use for quick visual arrangement. Avoid dragging an unselected object or an unintended group. |
| Rotate | Rotate selected symbols by 90 degrees. | Select the symbol, invoke Rotate, then inspect terminal orientation and drawing clarity. |
| Mirror H | Mirror selected symbols horizontally. | Use to improve drawing layout. Check that the symbol remains visually clear; mirroring is not a change in electrical polarity. |
| Mirror V | Mirror selected symbols vertically. | Use to improve drawing layout. Confirm that the symbol and terminal labels remain understandable. |
| Equipment | Open the Equipment Browser. | Search and select the required equipment type. |
| Zoom − | Zoom out. | See a larger portion of the SLD. |
| Zoom + | Zoom in. | Inspect a smaller area in more detail. |
| Fit | Fit the SLD drawing in the viewport. | Use when the drawing is outside the visible area or after a large edit. |
| Pan | Pan the viewport. | Reposition the view without moving objects. |
| Undo | Undo the last supported Application command. | Use immediately after an unintended command, then verify the result. |
| Redo | Redo an undone command. | Use only when the undone change is required. |
| Delete | Delete the selected engineering object through the supported route. | Confirm the selection and connected equipment before use. |
| Select All | Select all visible SLD objects. | Use for bulk presentation operations; inspect the selection before changing it. |
| Copy | Copy selected SLD representation. | Use where the editor supports representation copying. Verify identity and data after pasting. |
| Paste | Paste the copied representation. | Inspect the new object and do not assume its electrical connections were duplicated. |
| Cut | Copy and remove the selected SLD representation. | Use carefully; verify both the visual and engineering consequences. |
| Studies | Open Study Cases. | Create or select a study case. |
| SLD | Switch to SLD workspace. | Return to electrical drawing work. |
| Topology | Show topology projection. | Inspect network connectivity. |
| Map | Show persisted SLD geometry. | Inspect drawing/layout information. |
| Reports | Open study reports. | Review published results. |
| Control | Switch to Control workspace. | Work on ladder logic and control configuration. |
| Protection | Switch to Protection workspace. | Work on protection configuration and analysis. |

---

# 21. Equipment Library — equipment-by-equipment guide

The Equipment Library is a searchable catalogue. The current standard tool factory registry includes the equipment tool identifiers listed below. The actual entries shown to the operator depend on the equipment catalogue and the current Application composition. If a type is absent, do not assume that it can be created by typing its internal identifier.

## 21.1 Search and select an equipment type

1. Click the Equipment Browser/Equipment panel.
2. Click inside **Search components…**.
3. Enter a plain-language name such as `breaker`, `transformer`, `motor` or `current transformer`.
4. Read the displayed name and category.
5. Hover over an entry if you need its tooltip; it identifies the category, tool and symbol.
6. Click the required entry once.
7. Confirm that the creation tool becomes active.
8. Complete the draft workflow in the canvas and Properties panel.

A category heading is not an equipment entry. Clicking a category heading does not select a device.

## 21.2 Equipment catalogue reference

| Equipment entry | What it represents | Operator checks before committing |
|---|---|---|
| Bus | Common electrical node / busbar. | Correct nominal voltage, name and intended connections. |
| Line | Overhead or other line network element as configured by the catalogue/model. | From/to ends, length, voltage level and line electrical parameters. |
| Cable | Cable network element. | Cable type/conductor data, length, installation assumptions and electrical parameters. |
| Transformer | Power transformer connecting voltage levels. | Winding ratings, ratio, impedance, vector group, tap and grounding data. |
| Switch | Switching device. | Device identity, poles, operating state and in-service status. |
| Breaker | Circuit breaker. | Rated voltage/current, interrupting capability, poles, state and protection association where applicable. |
| Disconnector | Isolating device. | Correct terminal path, operating state and interlocking assumptions. |
| Fuse | Fuse/protective device. | Rated voltage/current, fuse characteristic and state. |
| Load | Electrical demand. | Active/reactive power, voltage and operating assumptions. |
| Generator | Generating source. | Rated values, voltage/setpoint and model parameters required by the intended study. |
| Synchronous Machine | Synchronous rotating machine model. | Machine ratings, electrical parameters and study-specific data. |
| Motor | Motor load / motor model. | Nameplate rating, voltage, power factor/efficiency and any model data required by the study. |
| Shunt | Shunt network element. | Type, rating, connection point and sign convention. |
| Capacitor | Capacitive compensation element. | Rated voltage, kvar/capacitance and switching state where applicable. |
| Reactor | Inductive shunt element. | Rated voltage, kvar/reactance and connection details. |
| Solar | Solar generation representation. | Rated power, connection bus and supported source/model parameters. |
| Battery | Battery/storage representation. | Power/energy ratings, operating assumptions and the supported model fields. |
| Grid | External grid/source representation. | Voltage, short-circuit strength/source impedance and reference assumptions. |
| Current Transformer (CT) | Current measurement instrument transformer. | Primary/secondary ratio, polarity, terminal identity, burden/class where supported. |
| Potential Transformer (PT/VT) | Voltage measurement instrument transformer. | Primary/secondary ratio, polarity, connection and grounding. |
| Capacitive Voltage Transformer (CVT) | Capacitive voltage measurement transformer. | Primary/secondary ratio, polarity, terminal identity and applicable model data. |
| Relay | Protection relay device. | Relay identity, protection-function configuration, measurement inputs and output/target mapping. |

## 21.3 Why CT, PT and CVT terminals matter

Instrument transformers have primary and secondary terminals. The primary side belongs to the electrical power circuit; the secondary side supplies a measurement circuit. Never connect primary and secondary terminals as though they were interchangeable.

For a CT, confirm P1/P2 and S1/S2 markings against the approved drawing. For a PT/CVT, confirm the primary and secondary terminal labels and the specified polarity. Incorrect polarity or ratio can invalidate protection and measurement results.

## 21.4 One-equipment-at-a-time workflow

For a first-time user, add one device at a time:

1. Search for the device.
2. Select it.
3. Complete its configuration.
4. Place it.
5. Verify its name and type in Project Explorer.
6. Save the project.
7. Continue with the next device.

This makes it easier to find which object caused a validation error.

---

# 22. Panel-by-panel reference

Panels display project information or provide a task-specific control surface. They do not all perform the same job.

## 22.1 Project Explorer

**Purpose:** Browse the project hierarchy.

The current hierarchy can contain:
- Project root — the active project name.
- Network Elements — grouped by equipment type.
- Documents — documents associated with the project.
- Study Cases — the study-case area and its workspace reference.

**How to use:**
1. Expand the project root if necessary.
2. Expand Network Elements.
3. Expand the relevant equipment-type group.
4. Click the required element.
5. Read the Properties panel.
6. If the canvas supports selection synchronization, the corresponding object is selected/highlighted there too.

**When to use:** When the drawing is crowded or when you know the object's name but cannot easily locate its symbol.

## 22.2 Equipment Browser

**Purpose:** Search the equipment catalogue and activate creation tools.

**Controls:**
- Search components… — filters by display name, category or equipment type.
- Equipment list — shows the matching catalogue entries grouped by category.
- Entry tooltip — shows the equipment name, category, tool identifier and symbol identifier.

**How to use:** Follow Chapter 21. Selecting an entry activates the corresponding tool; it does not itself commit the device.

## 22.3 Properties

**Purpose:** Inspect and configure the currently selected object or active draft.

The panel can show:
- Identity — the selected object's identifier.
- Type — its equipment type.
- Status — whether it is a draft or a committed object/status.
- Placement — the draft placement state, when applicable.
- Terminals — the declared terminal contract.
- Acquired Endpoints — endpoint references acquired by the active draft, when present.
- Connections — known connection references.
- Engineering Parameters — values and editability information.
- Validation text — configuration/commit feedback.
- SLD Data Annotations — annotation controls for a selected SLD node.

**Apply / Commit button:**
- In draft-creation mode it can be used to place the configured draft when placement information is available.
- In committed-object inspection mode it applies editable engineering parameter changes.
- The button is disabled when the current context has no applicable operation.

**Commit Network button:**
- Enabled when a draft network is available.
- Requests asynchronous validation/commit of the draft network.
- Changes its label to indicate that commitment is in progress.
- Shows success or failure feedback when the operation completes.

**Operating rule:** Do not treat the Apply / Commit and Commit Network buttons as interchangeable. Read the button label and validation text before pressing.

### SLD Data Annotations

When exactly one SLD node is selected, the annotation area can show:
- Block — identity of the annotation block.
- Fields — comma-separated data fields to display.
- Offset X / Offset Y — position offsets for the annotation.
- Visible — whether the annotation is displayed.
- Apply Annotation Changes — save the edited annotation settings.
- Remove Annotation — remove the selected annotation block.
- Add Data Annotation Block — create an annotation block for the selected node.

**How to use:**
1. Select one SLD node.
2. Find the SLD Data Annotations section.
3. Add a block if none exists.
4. Enter the fields that the current application supports for display.
5. Set visibility and offsets.
6. Click Apply Annotation Changes.
7. Inspect the canvas and adjust the offsets if required.

Annotations are presentation labels. They are not a substitute for changing the equipment's engineering parameters.

## 22.4 Element List

**Purpose:** Present a list-oriented view of engineering elements. Use it as an alternate way to inspect or locate elements where the panel is available.

The exact columns, sorting controls and selection gestures require running-UI verification before a future revision describes them.

## 22.5 Messages / Events

**Purpose:** Display messages and event feedback from application operations.

**How to use:**
1. Open the panel after a failed or unexpected operation.
2. Read the newest message and its complete text.
3. Note the affected operation/object.
4. Correct the underlying issue or stop and report it.
5. Do not clear or ignore a warning before understanding it.

The panel title is **Messages / Events** in the current default panel composition.

## 22.6 Study Cases

**Purpose:** Create, select and run study cases and inspect available results/archive entries.

The panel currently provides these fields and controls:

| Field/control | What to enter or do |
|---|---|
| Optional Study Case name | Enter a descriptive name, such as `Normal_Load_Flow`. |
| Study type | Choose Power Flow, Short-Circuit or Transient Stability. |
| Slack Bus (PF / transient init.) | Select the reference/slack bus for power-flow or transient initialization. |
| PV Bus IDs (comma-separated) | Enter the bus identifiers configured as PV buses, if required by the study. |
| System base MVA | Enter the system MVA base used by the study model. Confirm it against the approved study basis. |
| Fault Bus (short-circuit) | Select the bus where the fault is to be applied. |
| Fault type | Select 3PH, LG, LL or LLG as appropriate. |
| Fault resistance (Ω) | Enter the fault resistance in ohms. The field indicates a default of zero. |
| Fault reactance (Ω) | Enter the fault reactance in ohms. The field indicates a default of zero. |
| Transient end time (s) | Enter the simulation end time in seconds. The current UI default is 10.0 s. |
| Transient step (s) | Enter the simulation time step in seconds. The current UI default is 0.01 s. |
| Create Study Case | Create the study case using the selected study type and entered fields. |
| Study case list | Select the case to inspect or run. |
| Run Study | Run the selected case when its execution handler is available. |
| Study Results | Select/view results associated with the case. |
| Transient Result View | View transient-result presentation when a compatible result exists. |
| Archived Executions search | Search archived executions by study case, type, status or record ID. |
| Archived Executions list | Select one or more archived execution records. |
| Compare Selected Executions | Compare the selected archived executions. |

**Study-case procedure:**
1. Save the project.
2. Confirm the electrical network and equipment data.
3. Open Study Cases.
4. Enter a clear case name.
5. Choose the intended study type.
6. Enter only the fields relevant to that study.
7. Click Create Study Case.
8. Select the newly created case.
9. Click Run Study if enabled.
10. Read the execution status and diagnostics.
11. Select a result and review its assumptions and units.
12. Archive/compare only where the corresponding workflow is available.

Do not assume that every study type is executable for every network. A disabled action or failed validation must be investigated, not bypassed.

---

# 23. Control workspace — tools and controls

The Control workspace is intended for ladder/control logic and signal/action configuration. Its canvas is separate from the electrical SLD canvas.

## 23.1 Control toolbar

| Group | Control | Purpose |
|---|---|---|
| Rung | Add Rung | Add a new ladder rung. |
| Rung | Remove Rung | Remove the selected rung. |
| Rung | Move Up | Move the selected rung earlier/up in the rung order. |
| Rung | Enable / Disable | Toggle the selected rung's enabled state. |
| Tool | Cancel | Cancel transient Control tool state. |
| Study | Execute Cycle | Execute the current Control study cycle, if available. |
| History | Undo | Undo the last Application command. |
| History | Redo | Redo the last Application command. |

**Rung workflow:**
1. Activate Control workspace.
2. Add a rung.
3. Select the rung to inspect it.
4. Add components using the Control tool palette.
5. Arrange the components and connect their logic as supported by the editor.
6. Configure timers, signal bindings or action bindings in the Inspector.
7. Enable/disable the rung deliberately.
8. Execute the cycle only after reviewing the logic and signal mappings.

## 23.2 Control tool palette

The current Control tool registry defines these candidate tools. The palette displays only tools whose corresponding Application command/component capability is registered.

### Contacts
- **Normally Open Contact (NO):** A ladder contact that is logically true when its associated input condition is true. Use it for a normally-open contact condition.
- **Normally Closed Contact (NC):** A ladder contact that evaluates the inverse of its associated input condition. Verify the signal semantics before using it in a permissive or trip path.

### Coils and memory
- **Coil:** Represents a logic output driven by the rung condition.
- **Set Coil:** Sets/latches a logic state according to the configured component semantics.
- **Reset Coil:** Resets a latched logic state according to the configured component semantics.
- **Latch / SR:** Stores a set/reset state. Verify set/reset priority and reset conditions before use in a safety-related circuit.

### Timers
- **TON Timer:** On-delay timer; its output changes after the input condition has remained true for the configured delay.
- **TOF Timer:** Off-delay timer; its output remains active for the configured delay after the input condition becomes false.
- **TP Timer:** Pulse timer; generates a pulse for a configured duration after a trigger.

### Logic gates
- **AND:** Output is true only when all required inputs are true.
- **OR:** Output is true when at least one required input is true.
- **NOT:** Inverts a logic input.
- **XOR:** Output is true when the inputs differ, for the supported input count/semantics.

### Interlocking and signal actions
- **Interlock:** Represents an interlock logic component. Define its permissive/trip meaning explicitly.
- **Control Interlock:** Configure a control interlock through the Inspector.
- **Connect Signal:** Connect an engineering signal to a Control input.
- **Disconnect Signal:** Remove the selected signal connection.
- **Action Binding:** Bind a logic output to a supported equipment action.
- **Move Component:** Move a selected logic component.
- **Remove Component:** Remove a selected logic component.

## 23.3 Control Inspector

The Control Inspector is contextual: select a rung or component to display its details.

Current controls include:
- Component identity and type.
- Configuration display.
- Rung identity, order, enabled state and component count.
- Preset -0.5 / Preset +0.5 — adjust the selected timer preset in half-unit steps.
- Cycle TON / TOF / TP — cycle the selected timer mode.
- Apply Timer Configuration — apply the selected timer's configuration.
- Logic output — list outputs available from the selected component.
- Action target — list eligible equipment targets.
- Action — choose an available action for the selected target.
- Create Action Binding — bind the selected logic output to the chosen equipment action.
- Create Interlock — create an interlock where the Application supports it.
- Engineering signal source — choose an engineering signal source.
- Selected Control component input — choose the destination input.
- Control action / interlock destination — choose the action/interlock destination.
- Project engineering signal bindings — review existing mappings.
- Add / Update Engineering Signal Binding — create or update the selected mapping.
- Remove Selected Signal Binding — remove the selected mapping.

**Control safety rule:** An action binding is a configured command relationship. It is not proof that a physical device received, accepted or completed the command. Verify the feedback/acknowledgement path independently.

---

# 24. Protection workspace — tools and panels

The Protection workspace presents the protection system as a relationship between measurement channels, relay inputs, protection functions, decisions and trip requests.

## 24.1 Protection interaction tools

| Tool | Purpose | How to use |
|---|---|---|
| Select | Select a Protection object. | Activate Select and click the object. |
| Connect Measurement | Bind a measurement channel to a relay input. | Select the measurement channel first, then select the intended relay input. Review the binding and resulting diagnostics. |
| Inspect | Select an object for inspection. | Activate Inspect and select the item whose details you need. |
| Fit | Fit the Protection view to its content. | Use when nodes are outside the visible area. |
| Diagnostics | Show Protection diagnostics. | Use to inspect missing configuration, measurement or dispatch information. |

### Connect Measurement — exact order

1. Activate Connect Measurement.
2. Click the intended Measurement Channel node.
3. Confirm the preview/status message identifies that channel.
4. Click the intended Relay Input node.
5. Confirm the application accepts the binding.
6. Inspect the resulting relay input/configuration.
7. Confirm that the intended protection element uses the correct channel.

If you select a relay input first, the tool reports that a MeasurementChannel must be selected first. If you click an unrelated node, the operation is rejected with feedback.

## 24.2 Protection presentation nodes

The Protection canvas can show:
- Measurement Channel.
- Relay Input.
- Relay.
- Protection Element / function code.
- Decision.
- Trip Request / Application boundary.
- Protection configuration status, including an explicit uncommissioned/no-function-configuration indication.

These nodes are a projection of the Application read model. A line between nodes represents the displayed engineering relationship; it is not by itself proof of physical wiring, a field-device command or a successful breaker operation.

## 24.3 Protection engineering panels

The Protection workspace source composes engineering panels for:
- **Protection Analysis Coverage:** review which protection analysis/model paths are covered or unsupported.
- **Protection Function Catalog:** inspect the available protection functions.
- **Protection TCC:** inspect time-current characteristic information where applicable.
- **Protection Coordination Study:** configure/review protection coordination study information.

A TCC (time-current characteristic) is a curve relating current magnitude to operating time. The current TCC view identifies inverse-time curves for ANSI 51 and 51N. Other functions can produce a notice that they do not use an inverse-time TCC in this view.

Do not infer a complete protection coordination approval from a displayed curve alone. Confirm CT data, relay settings, fault levels, breaker clearing time, grading margins and study coverage.

---

# 25. Keyboard shortcuts reference

Shortcuts below are declared in the current application menu specification.

| Shortcut | Command |
|---|---|
| Ctrl+N | New Project |
| Ctrl+O | Open Project |
| Ctrl+S | Save Project |
| Ctrl+Shift+S | Save Project As |
| Ctrl+W | Close Project |
| Alt+F4 | Exit |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Delete | Delete Selection |
| Ctrl+A | Select All |
| Ctrl+C | Copy |
| Ctrl+V | Paste |
| Ctrl+X | Cut |
| Ctrl+Space | Maximize Editor |
| Ctrl+Shift+Enter | Commit Draft |

The tool-shortcut registry supports contextual keymaps for global, SLD, Control, Protection, Study, Canvas, Inspector and Tool Shelf contexts. Do not publish a shortcut for an individual tool unless it is actually registered in the running release. Tooltips may display a shortcut when one is assigned.

---

# 26. Tooltips, icons and visual states

## 26.1 Tooltips

A tooltip is the short explanation shown when the pointer rests over a button or tool. In GridForge, tooltips can include:
- Tool/action name.
- Assigned keyboard shortcut.
- Short description.

Use tooltips as a quick reminder, not as a substitute for the full instructions in this manual.

## 26.2 Active tool state

A checkable tool button can appear pressed or highlighted while it is active. This indicates the current interaction mode, not that an electrical operation has been committed.

Before clicking the canvas, look at the active tool name. If you intend to select an existing object, activate Select first.

## 26.3 Disabled controls

A disabled/greyed control means the action is not currently available. Common reasons include:
- No active project.
- No object selected.
- No draft network available.
- No editable parameter.
- Required Application command not registered.
- The current editor does not support that tool.
- An operation is still running.

Do not attempt to bypass disabled controls. Satisfy the missing context or read the relevant diagnostic.

## 26.4 Icon identification

Icon artwork can vary with theme, display scale and icon-provider configuration. Use the adjacent text or tooltip as the authoritative label. If an icon is missing or visually ambiguous, report the screen, workspace, button tooltip and application build rather than guessing its function.

---

# 27. Detailed documentation and verification register

The following items must be checked in the running application before their mouse gestures, exact icon artwork or all field-level behaviour can be called final:

1. Capture the full menu bar and each menu opened, including enabled/disabled states.
2. Capture the SLD toolbar and identify every visible icon by its tooltip.
3. Demonstrate each toolbar action on a disposable sample project.
4. Demonstrate selection, box selection, move, drag move, rotate, mirror, copy, cut, paste, delete, zoom, fit and pan.
5. Demonstrate each equipment type from search through draft, placement, commit and re-selection.
6. Record every editable parameter, unit, allowed range, default and validation message for each equipment type.
7. Demonstrate each panel open/close, resize, dock/float and workspace-region behaviour.
8. Demonstrate all Study Case fields and the successful/failed/unsupported execution paths.
9. Demonstrate all Control palette tools, rung actions, timer configuration, signal mapping and action binding.
10. Demonstrate Protection measurement binding, diagnostics, function configuration and TCC/coordination workflows.
11. Capture the status bar, messages, tool settings and context menus where present.
12. Verify every shortcut in the running application; remove any shortcut that conflicts with the operating system or another editor.
13. Add a screenshot immediately after each major procedure, with numbered callouts and matching step numbers.
14. Recheck every procedure after changes to menu/action IDs, tool definitions, panel composition or workspace layout.

## 27.1 Screenshot standard

Each screenshot must:
- come from the actual GridForge application, not a mock-up;
- show the relevant menu, panel or canvas state;
- have readable text at normal document zoom;
- use numbered callouts that match the procedure;
- avoid confidential plant/project information unless the owner has approved its use;
- be updated when the UI changes.

## 27.2 Manual completeness rule

A tool or menu is not documented merely because its name appears in a table. A complete entry must explain purpose, prerequisites, activation, click/keyboard sequence, expected screen response, engineering effect, validation, cancellation/recovery and common mistakes.

**This manual remains a working operator handbook until the verification register is completed against the actual running UI.**
