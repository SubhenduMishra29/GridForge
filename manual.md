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
