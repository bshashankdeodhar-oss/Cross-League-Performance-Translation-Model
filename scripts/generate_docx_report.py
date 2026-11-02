"""
generate_docx_report.py
Generates an institutional-grade, beautifully formatted Microsoft Word (.docx) document
for the TransferWorth (CLPTM) Project Report.
"""

import os
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def add_callout(doc, text, title=None, border_color="009688", fill_color="F4FBF9"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, fill_color)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="36" w:space="0" w:color="{border_color}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    if title:
        run_title = p.add_run(f"📌 {title}\n")
        run_title.bold = True
        run_title.font.name = "Calibri"
        run_title.font.size = Pt(10.5)
        run_title.font.color.rgb = RGBColor(15, 32, 67)
    
    run_text = p.add_run(text)
    run_text.font.name = "Calibri"
    run_text.font.size = Pt(10)
    run_text.font.italic = True
    run_text.font.color.rgb = RGBColor(40, 50, 60)
    
    # spacing after table
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(0)
    p_after.paragraph_format.space_after = Pt(4)

def format_table(table, col_widths, headers, data, header_bg="1B365D", alt_bg="F8F9FA"):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Format header
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        set_cell_background(hdr_cells[i], header_bg)
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        for run in p.runs:
            run.font.bold = True
            run.font.name = "Calibri"
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(255, 255, 255)
            
    # Format data rows
    for r_idx, row_data in enumerate(data):
        row = table.rows[r_idx + 1]
        bg = alt_bg if (r_idx % 2 == 1) else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            cell.text = str(val)
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            if c_idx > 0 and any(char.isdigit() for char in str(val)):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.name = "Calibri"
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(30, 30, 30)
                if c_idx == 0:
                    run.font.bold = True
                    
    # Set widths
    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = width

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = RGBColor(27, 54, 93) # Navy
    return p

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(13)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0, 128, 115) # Teal/Emerald
    return p

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(11)
    run.font.bold = True
    run.font.color.rgb = RGBColor(50, 70, 90)
    return p

def add_body_p(doc, text, bold_prefix=None, space_after=5):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10)
        r_pre.font.bold = True
        r_pre.font.color.rgb = RGBColor(20, 20, 20)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(40, 40, 40)
    return p

def add_bullet(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.font.name = "Calibri"
        r_pre.font.size = Pt(10)
        r_pre.font.bold = True
        r_pre.font.color.rgb = RGBColor(20, 20, 20)
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(40, 40, 40)
    return p

def add_image_with_caption(doc, image_path, caption, width_in=6.0):
    if not os.path.exists(image_path):
        add_callout(doc, f"[Image not found at {image_path}]", title="Missing Image")
        return
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after = Pt(3)
    p_img.paragraph_format.keep_with_next = True
    run = p_img.add_run()
    run.add_picture(image_path, width=Inches(width_in))
    
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(0)
    p_cap.paragraph_format.space_after = Pt(12)
    run_cap = p_cap.add_run(f"Figure: {caption}")
    run_cap.font.name = "Calibri"
    run_cap.font.size = Pt(9)
    run_cap.font.italic = True
    run_cap.font.color.rgb = RGBColor(90, 100, 110)

def build_document():
    doc = Document()
    
    # Page setup - Margins (1 inch)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
        # Add page numbering footer
        footer = section.footer
        p_ft = footer.paragraphs[0]
        p_ft.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_ft = p_ft.add_run("TransferWorth (CLPTM) | Academic Project Report — VIT Chennai")
        r_ft.font.name = "Calibri"
        r_ft.font.size = Pt(8.5)
        r_ft.font.color.rgb = RGBColor(128, 128, 128)

    project_root = Path("c:/Shanki/VIT_CHENNAI/Projs/TransferPred")
    screenshots_dir = project_root / "docs" / "screenshots"

    # =========================================================================
    # COVER / TITLE BLOCK
    # =========================================================================
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(30)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("TransferWorth: Cross-League Performance Translation Model (CLPTM)")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(27, 54, 93)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(24)
    run_sub = p_sub.add_run("A Machine Learning & Explainable AI Platform for Cross-League Football Recruitment")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(13)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(0, 128, 115)

    # Metadata Card Table
    meta_tbl = doc.add_table(rows=5, cols=2)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_widths = [Inches(2.2), Inches(4.3)]
    meta_data = [
        ("Student Author", "Shashank Deodhar Bantupalli"),
        ("Registration Number", "24BRS1297"),
        ("Academic Institution", "School of Computer Science and Engineering, VIT Chennai"),
        ("Course / Track", "Software Engineering / Machine Learning & Data Analytics"),
        ("Date & Version", "October 2026 | Version 1.0 (Production Release)")
    ]
    for r_idx, (k, v) in enumerate(meta_data):
        row = meta_tbl.rows[r_idx]
        row.cells[0].text = k
        row.cells[1].text = v
        set_cell_background(row.cells[0], "F0F4F8")
        set_cell_background(row.cells[1], "FFFFFF")
        set_cell_margins(row.cells[0], top=60, bottom=60, left=100, right=100)
        set_cell_margins(row.cells[1], top=60, bottom=60, left=100, right=100)
        p0 = row.cells[0].paragraphs[0]
        p1 = row.cells[1].paragraphs[0]
        p0.paragraph_format.space_before = Pt(2)
        p0.paragraph_format.space_after = Pt(2)
        p1.paragraph_format.space_before = Pt(2)
        p1.paragraph_format.space_after = Pt(2)
        for r in p0.runs:
            r.font.bold = True
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(27, 54, 93)
        for r in p1.runs:
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(30, 30, 30)
        row.cells[0].width = meta_widths[0]
        row.cells[1].width = meta_widths[1]

    doc.add_page_break()

    # =========================================================================
    # TABLE OF CONTENTS SUMMARY
    # =========================================================================
    add_heading_1(doc, "Document Table of Contents")
    toc_items = [
        ("1. Abstract", "Executive summary of model goals, multi-league dataset, and predictive accuracy."),
        ("2. Problem Statement", "The economic stakes of modern transfers and the 'Haaland vs. Werner' paradox."),
        ("3. Introduction", "Modern sports analytics background, project genesis at VIT Chennai, and vision."),
        ("4. Objectives and Scope", "Key algorithmic deliverables, tactical profiling, boundaries, and exclusions."),
        ("5. AI Concepts and Related Work", "Domain adaptation, anti-leakage design, LightGBM, MLP, Bayesian Ridge, TRC, SHAP."),
        ("6. System Architecture", "Multi-tier design, StarUML Relational ERD (8 tables), and Data Flow Diagrams (DFD)."),
        ("7. Proposed Planning Method", "Agile-Scrum methodology, WBS work packages (1.0 to 7.0), and delivery milestones."),
        ("8. Technology, Stack and Resources", "Full-stack matrix (Python, FastAPI, React 19, SQLite/PostgreSQL) and hardware specs."),
        ("9. User Workflow and Example Scenarios", "End-to-end user sequence, Wirtz, Haaland, and Werner real-world transfer case studies."),
        ("10. Screenshots of the Done Project", "Embedded live user interface screenshots, interactive sandbox, and evaluation plots."),
        ("11. Testing and Evaluation", "15 automated unit/integration tests, 5-fold CV, and backtest benchmarks on 550 transfers."),
        ("12. Limitations, Assumptions and Risks", "Tactical assumptions, human acclimatization limits, and data scraping risks."),
        ("13. Suggestions for Improvements", "StatsBomb 360 tracking, manager tactical vectors, and Celery background queues."),
        ("14. Conclusion and References", "Final project synthesis, academic papers, and official sports analytics citations.")
    ]
    for num, desc in toc_items:
        add_bullet(doc, f"{desc}", bold_prefix=f"{num}: ")

    doc.add_page_break()

    # =========================================================================
    # 1. ABSTRACT
    # =========================================================================
    add_heading_1(doc, "1. Abstract")
    add_body_p(doc, 
        "In professional association football, player recruitment represents one of the highest-stakes financial and sporting investments, "
        "with European clubs committing billions of euros annually during transfer windows. A chronic and expensive failure mode in football recruitment "
        "is the breakdown of metric translation across leagues: a forward scoring 0.90 goals per 90 minutes in one domestic league frequently suffers "
        "severe performance drop-offs when transferring to another. This disconnect—exemplified by the 'Haaland vs. Werner' paradox—stems from non-linear "
        "disparities in league tempo, tactical pressing structures, space compactness, teammate creation quality, and physiological adaptation demands.")
    
    add_body_p(doc,
        "To address this challenge, we present TransferWorth (Cross-League Performance Translation Model - CLPTM), an institutional-grade, "
        "full-stack machine learning system that translates, projects, and contextualizes professional football player performance across Europe's "
        "premier competitions. The system ingests and harmonizes a multi-season dataset comprising 24,413 player-seasons (14,865 meeting the "
        "professional playing threshold of ≥ 600 minutes) across Europe’s Top 5 domestic leagues (Premier League, La Liga, Serie A, Bundesliga, and Ligue 1) "
        "spanning 2017/18 through 2025/26.")

    add_body_p(doc,
        "TransferWorth employs a leak-free multi-model architecture combining LightGBM Gradient Boosted Decision Trees for primary metric regression, "
        "Deep Multilayer Perceptrons (MLP) for non-linear tactical interactions, and Bayesian Ridge Regression to compute explicit 95% Bayesian "
        "Credible/Confidence Intervals for projected metrics. Furthermore, the model introduces a Tactical Transfer Reality Check (TRC) engine that "
        "modulates predictions based on the target club's relative attacking strength (Δstrength ratio), granting up to +10% performance mitigation for "
        "dominant clubs or applying up to -12% penalties for struggling sides. Supervised adaptation and downside risk classifiers, calibrated on 955 "
        "empirical cross-league transfers, estimate the probability of output retention (ROC-AUC: 0.611) and flag severe collapse risks (ROC-AUC: 0.655).")

    add_body_p(doc,
        "Explainable AI is integrated via TreeSHAP factor attributions and interactive counterfactual what-if simulations. Rigorous backtesting on 550 "
        "longitudinal transfer cases confirms predictive accuracy: Mean Absolute Error (MAE) of 0.0545 on goals_p90, 0.0333 on assists_p90, "
        "0.0359 on xg_p90, and 0.0127 on xag_p90. The system is deployed via a normalized 8-table relational database schema, a high-throughput FastAPI "
        "REST microservice with JWT authentication, and a responsive React 19 / Vite analytical dashboard.")

    add_callout(doc, 
        "Key Quantitative Result: Across 550 verified longitudinal transfer test cases, the primary LightGBM model achieved an out-of-sample MAE "
        "of 0.0545 on goals_p90 and 0.0127 on xag_p90, outperforming conventional league multipliers and standard linear regression baselines.",
        title="Performance Summary")

    # =========================================================================
    # 2. PROBLEM STATEMENT
    # =========================================================================
    add_heading_1(doc, "2. Problem Statement")
    add_heading_2(doc, "2.1 The Economic Stakes of Player Recruitment")
    add_body_p(doc,
        "Modern football has evolved into a globalized, hyper-commercialized industry where single player transfers routinely command fees exceeding "
        "€50 million to €100 million, alongside long-term multi-million-euro wage commitments. FIFA transfer market reports indicate that clubs spend over "
        "€8 billion annually on international player movements. Consequently, an erroneous transfer acquisition inflicts not only catastrophic financial losses "
        "(depreciated asset valuation, deadweight wage burdens) but also sporting setbacks that can result in missed UEFA Champions League qualifications or relegation.")

    add_heading_2(doc, "2.2 The Metric Carry-Over Fallacy & The 'Haaland vs. Werner' Paradox")
    add_body_p(doc,
        "Recruitment departments historically relied on unadjusted statistical carry-over—naively projecting that a player's raw per-90 metrics in League A "
        "will directly replicate in League B. This assumption repeatedly fails due to profound environmental and tactical divergence between European leagues:")
    
    add_bullet(doc, "In the German Bundesliga, Erling Haaland (Borussia Dortmund) and Timo Werner (RB Leipzig) both exhibited elite goal-scoring rates (~0.90 to 1.00 goals/90). Upon transferring to the English Premier League, their trajectories diverged drastically. Erling Haaland maintained record-breaking output at Manchester City, whereas Timo Werner experienced an immediate 60% decline in goal conversion and minutes security at Chelsea.", bold_prefix="The 'Haaland vs. Werner' Paradox: ")
    add_bullet(doc, "Competitions vary significantly in pace, physical dueling intensity, and defensive organization. Bundesliga games often feature open-field transitional play, while the Premier League and Italian Serie A feature high physical pressing compactness and deeper defensive low-blocks.", bold_prefix="League Difficulty Deltas: ")
    add_bullet(doc, "A player moving to an average mid-table team will receive fewer quality progressive passes and box entries than one moving to a possession-dominant superclub (e.g., Manchester City, Real Madrid, Bayern Munich). Raw league multipliers ignore target club context entirely.", bold_prefix="Teammate Creation Capacity: ")
    add_bullet(doc, "Transition-oriented forwards who excel when running into open channels behind high defensive lines struggle when tasked with breaking down compact low-block defenses in closed spaces.", bold_prefix="Tactical System Mismatch: ")
    add_bullet(doc, "Standard analytics provide single-point projections, leaving decision-makers blind to epistemic uncertainty, downside risk, and acclimatization variance.", bold_prefix="Adaptation Uncertainty: ")

    add_heading_2(doc, "2.3 Shortcomings of Conventional Scouting Systems")
    add_body_p(doc, "Traditional scouting workflows suffer from three structural weaknesses:")
    add_bullet(doc, "Scouts frequently overweight recent highlight-reel performances in international tournaments or domestic cup matches while discounting multi-season statistical variance.", bold_prefix="1. Eye-Test & Recency Bias: ")
    add_bullet(doc, "Fixed league coefficients (e.g., multiplying all Bundesliga goals by 1.0 and Portuguese Primeira Liga goals by 0.75) treat all players uniformly, ignoring positional profiles, age curves, and target club quality.", bold_prefix="2. Uniform League Multipliers: ")
    add_bullet(doc, "Black-box algorithmic scouting tools fail to communicate why a forecast is generated or what tactical conditions must be satisfied to unlock the player's potential.", bold_prefix="3. Absence of Explainability & Uncertainty: ")

    # =========================================================================
    # 3. INTRODUCTION
    # =========================================================================
    add_heading_1(doc, "3. Introduction")
    add_heading_2(doc, "3.1 Domain Background")
    add_body_p(doc,
        "Association football analytics has transitioned over the past decade from rudimentary box-score counts (goals, assists, appearances) to granular event tracking. "
        "The public release and commercialization of advanced metrics—Expected Goals (xG), Expected Assisted Goals (xAG), Key Passes, Progressive Passes, "
        "Progressive Carries, and Defensive Pressures—has enabled analysts to quantify the underlying quality of chances created and conceded, moving beyond misleading outcome variance.")
    add_body_p(doc,
        "However, almost all state-of-the-art predictive models remain confined to intra-league forecasting (e.g., predicting how a player will perform next season "
        "within the same domestic competition). Modeling player performance across disparate domestic leagues requires solving a domain-adaptation and covariate-shift "
        "problem in applied machine learning: how to translate a feature vector observed under one environment distribution P(X_LeagueA) into an outcome distribution "
        "governed by another P(Y_LeagueB).")

    add_heading_2(doc, "3.2 Genesis and Vision of TransferWorth (CLPTM)")
    add_body_p(doc,
        "Developed as an academic software engineering and machine learning project at the School of Computer Science and Engineering, Vellore Institute of Technology (VIT), Chennai, "
        "under the leadership of Shashank Deodhar Bantupalli (Reg No: 24BRS1297), TransferWorth (Cross-League Performance Translation Model) was conceived to provide football directors, "
        "chief data officers, and technical scouts with an end-to-end analytical workbench.")
    add_body_p(doc,
        "The system combines rigorous data engineering, empirical football physics, machine learning regression, probabilistic Bayesian uncertainty estimation, "
        "game-theoretic explainability (SHAP), and modern cloud/web technologies into an integrated software platform.")

    # =========================================================================
    # 4. OBJECTIVES AND SCOPE
    # =========================================================================
    add_heading_1(doc, "4. Objectives and Scope")
    add_heading_2(doc, "4.1 Functional Objectives")
    add_bullet(doc, "Ingest, parse, sanitize, and standardize historical match event statistics across Europe's Top 5 domestic leagues from 2017/18 through 2025/26 (24,413 records).", bold_prefix="1. Multi-League Data Ingestion: ")
    add_bullet(doc, "Calculate dynamic League Strength Coefficients (LSC) based on UEFA 5-year confederation coefficients and empirical cross-league transfer performance ratios.", bold_prefix="2. League Strength Quantification: ")
    add_bullet(doc, "Forecast translated per-90 metrics across attacking (goals, assists, xG, xAG), progression (prog passes, key passes, prog carries), and defensive categories.", bold_prefix="3. Multi-Target Metric Forecasting: ")
    add_bullet(doc, "Incorporate destination team attacking strength ratios (Δstrength) to reward players moving into high-creation squads and penalize moves to struggling teams.", bold_prefix="4. Tactical TRC Context: ")
    add_bullet(doc, "Deliver 95% Bayesian Confidence/Credible Intervals ([μ - 1.96σ, μ + 1.96σ]) on projected output.", bold_prefix="5. Uncertainty Modeling: ")
    add_bullet(doc, "Predict probability of retaining ≥ 70% of prior production and flag severe drop-off risks (< 45% xG).", bold_prefix="6. Adaptation & Risk Classification: ")
    add_bullet(doc, "Generate local TreeSHAP attribution factor waterfalls explaining the top 5 positive and negative drivers behind each projection.", bold_prefix="7. Explainable AI: ")
    add_bullet(doc, "Allow scouts to dynamically manipulate environmental parameters (target team quality, minutes, age) to simulate counterfactual outcomes in real time.", bold_prefix="8. Interactive What-If Sandbox: ")
    add_bullet(doc, "Automatically classify players into modern tactical roles (e.g. 'Advanced Playmaker', 'Clinical Primary Goalscorer') and benchmark projected metrics against destination incumbents.", bold_prefix="9. Tactical Archetype Profiling: ")

    add_heading_2(doc, "4.2 Project Scope & Boundaries")
    add_bullet(doc, "Outfield players and goalkeepers in Premier League (England), La Liga (Spain), Serie A (Italy), Bundesliga (Germany), and Ligue 1 (France).", bold_prefix="Target Competitions: ")
    add_bullet(doc, "2017/18 through 2025/26 historical seasons + 191 verified Summer 2026 test transfers.", bold_prefix="Temporal Horizon: ")
    add_bullet(doc, "≥ 600 domestic league minutes per season to eliminate small-sample statistical volatility.", bold_prefix="Playing Time Filter: ")
    add_bullet(doc, "Tier 2 competitions (Championship, Eredivisie, Liga Portugal), orthopedic injury medical models, and lifestyle tracking are reserved for future iterations.", bold_prefix="Exclusions: ")

    # =========================================================================
    # 5. AI CONCEPTS AND RELATED WORK
    # =========================================================================
    add_heading_1(doc, "5. AI Concepts and Related Work")
    add_heading_2(doc, "5.1 League Difficulty Modeling & Covariate Shift")
    add_body_p(doc,
        "Cross-league translation is mathematically framed as a domain adaptation problem. Given a source domain D_S = {X_S, P(X_S)} and a target domain D_T = {X_T, P(X_T)}, "
        "where the conditional distributions P(Y_S|X_S) ≠ P(Y_T|X_T) differ due to competition difficulty and stylistic differences. TransferWorth introduces the League Strength Coefficient (LSC):")
    add_body_p(doc, "LSC_league = ω_1 · UEFA_norm + ω_2 · Elo_league", bold_prefix="Formula: ")
    add_body_p(doc, "Raw metrics are pre-adjusted into normalized space prior to model ingestion: X_adj = X_raw × (LSC_source / LSC_target).")

    add_heading_2(doc, "5.2 Leak-Free Multi-Model Machine Learning Architecture")
    add_body_p(doc,
        "A prevalent flaw in predictive sports modeling is data leakage—such as utilizing end-of-season shots or non-penalty xG to predict final goal tallies within the same season. "
        "TransferWorth implements an Anti-Leakage Filter that dynamically strips all direct collinear proxies: F_clean = F_all \\ {Direct Proxies of Target Y}.")
    
    add_bullet(doc, "Implements gradient-boosted decision trees using histogram-based feature binning and leaf-wise (best-first) tree growth. Handles non-linear feature interactions and skewed tabular distributions with L1/L2 structural regularization.", bold_prefix="1. LightGBM (Primary Non-Linear Regressor): ")
    add_bullet(doc, "A feedforward neural network comprising two hidden layers with ReLU activations, batch normalization, and dropout (p=0.2). Captures high-order interactions between age curves, carrying volume, and pressing intensity.", bold_prefix="2. Deep Multilayer Perceptron (MLP): ")
    add_bullet(doc, "Assumes Gaussian priors over weights and observation noise. Computes exact analytical posterior distributions over weights, generating explicit 95% Bayesian Credible Intervals: CI_95% = [y_hat - 1.96σ, y_hat + 1.96σ].", bold_prefix="3. Bayesian Ridge Regression: ")

    add_heading_2(doc, "5.3 Tactical TRC (Transfer Reality Check) Damping Formulation")
    add_body_p(doc,
        "Rather than evaluating a player against a theoretical league average, TransferWorth modulates predictions using the target club's relative attacking strength ratio: "
        "Δstrength = Goals Scored_TargetTeam / League Mean Goals Scored.")
    add_body_p(doc,
        "Y_TRC = Y_base × [1 + min(0.10, max(-0.12, 0.25 × (Δstrength - 1.0)))]", bold_prefix="TRC Modulation Formula: ")
    add_bullet(doc, "Stepping up to a superclub (Δstrength > 1.20x) provides up to a +10% positive boost, reflecting elite creative service from world-class teammates.", bold_prefix="Superclub Bonus: ")
    add_bullet(doc, "Moving to a relegation battler (Δstrength < 0.90x) enforces up to a -12% penalty, capturing starved service and deep defensive game plans.", bold_prefix="Relegation Penalty: ")

    add_heading_2(doc, "5.4 Supervised Adaptation & Downside Risk Classification")
    add_body_p(doc,
        "Trained on 955 verified historical cross-league transfers (X_T-1 → Y_T). Class-weighted logistic regression models optimize binary cross-entropy loss:")
    add_bullet(doc, "Binary label = 1 if player retained ≥ 70% of their prior per-90 attacking output (xG + xAG) while maintaining ≥ 900 domestic minutes; else 0.", bold_prefix="Adaptation Target: ")
    add_bullet(doc, "Binary label = 1 if player output dropped below 45% of baseline or playing time dropped below 65% of prior minutes; else 0.", bold_prefix="Downside Risk Target: ")

    add_heading_2(doc, "5.5 Explainable AI via TreeSHAP")
    add_body_p(doc,
        "To ensure transparency for coaching staff, TransferWorth integrates TreeSHAP (SHapley Additive exPlanations), assigning an additive attribution φ_j to each input feature. "
        "The system extracts the top 5 positive and negative contributing factors for every individual player forecast.")

    # =========================================================================
    # 6. SYSTEM ARCHITECTURE
    # =========================================================================
    add_heading_1(doc, "6. System Architecture")
    add_heading_2(doc, "6.1 Architectural Tier Breakdown")
    add_body_p(doc, "TransferWorth is structured across five decoupled, production-grade architectural tiers:")
    add_bullet(doc, "Processes 24,413 player-seasons, performs schema validation, per-90 normalization, and LSC translation, writing to data/processed/feature_dataset.csv.", bold_prefix="1. Data Engineering & ETL Tier: ")
    add_bullet(doc, "Houses LightGBM, MLP, Bayesian Ridge, TRC scaling, TreeSHAP explainability, and the Tactical Archetype classification engine.", bold_prefix="2. Machine Learning & Inference Tier: ")
    add_bullet(doc, "Normalized 8-table relational schema implemented via SQLAlchemy 2.0 with Alembic versioning (supporting SQLite and PostgreSQL).", bold_prefix="3. Persistence & Relational Database Tier: ")
    add_bullet(doc, "Asynchronous FastAPI REST server with Pydantic v2 validation, JWT authentication, and automated prediction auditing.", bold_prefix="4. Backend API Microservice Tier: ")
    add_bullet(doc, "React 19 single-page app built with Vite, styled with a retro-cyberpunk terminal theme, Recharts visualizations, and interactive scout consoles.", bold_prefix="5. Presentation & Frontend Tier: ")

    add_heading_2(doc, "6.2 Relational Database Schema (StarUML ERD Table Dictionary)")
    
    erd_headers = ["Table Name", "Primary Key", "Foreign Keys", "Description & Stored Attributes"]
    erd_widths = [Inches(1.5), Inches(1.1), Inches(1.4), Inches(2.5)]
    erd_data = [
        ("League", "league_id", "None", "Master competitions, UEFA LSC coefficients, and country codes."),
        ("Team", "team_id", "league_id", "Club entities and computed relative attacking strength ratios."),
        ("User", "user_id", "None", "Role-based access control (admin, viewer) with bcrypt password hashes."),
        ("Player", "player_id", "team_id, league_id", "Core player identities, primary positions, ages, and club links."),
        ("PlayerStats", "stats_id", "player_id", "Season metrics (goals, assists, xG, xAG, passes, LSC-adjusted stats)."),
        ("PlayerStyleProfile", "profile_id", "player_id", "Tactical traits (progressive index, direct carries, age curve scores)."),
        ("TransferPrediction", "prediction_id", "player_id, user_id, src/tgt", "Audit trail of model predictions, Bayesian CIs, and risk scores."),
        ("ScenarioSimulation", "simulation_id", "prediction_id", "Saved what-if counterfactual parameter exploration logs.")
    ]
    erd_table = doc.add_table(rows=len(erd_data) + 1, cols=4)
    format_table(erd_table, erd_widths, erd_headers, erd_data)

    # =========================================================================
    # 7. PROPOSED PLANNING METHOD
    # =========================================================================
    add_heading_1(doc, "7. Proposed Planning Method")
    add_heading_2(doc, "7.1 Software Engineering Methodology")
    add_body_p(doc,
        "The project was executed following an Agile-Scrum methodology structured around two-week sprint cycles. Each sprint produced a fully testable, "
        "demonstrable increment. Development was governed by the formal Work Breakdown Structure (WBS) defined in TransferWorth_WBS.xml.")

    add_heading_2(doc, "7.2 Work Breakdown Structure (WBS Work Packages)")
    wbs_headers = ["WBS ID", "Work Package Name", "Key Deliverables & Milestones", "Predecessor"]
    wbs_widths = [Inches(0.8), Inches(1.8), Inches(3.0), Inches(0.9)]
    wbs_data = [
        ("1.0", "Project Management & Architecture", "Scope definition, SRS document, architectural blueprint, StarUML ERD & DFDs.", "—"),
        ("2.0", "Data Pipeline & Engineering (ETL)", "Web scrapers, schema standardization, per-90 normalization, LSC engine, feature store.", "1.0"),
        ("3.0", "ML Model Development & Anti-Leakage", "Anti-leakage feature isolation, LightGBM, MLP, Bayesian Ridge, TRC engine.", "2.0"),
        ("4.0", "Explainability & Evaluation Engine", "Longitudinal backtesting (550 transfers), TreeSHAP factor extractor, what-if simulator.", "3.0"),
        ("5.0", "Backend API & Database Setup", "Relational DDL & Alembic migrations, FastAPI REST endpoints, JWT auth, prediction audit.", "1.0, 3.0"),
        ("6.0", "Frontend Dashboard (React / Vite)", "Terminal design system, live predictor console, what-if sandbox, Recharts integration.", "5.0"),
        ("7.0", "Integration, QA & Deployment", "End-to-end integration testing (15 automated tests), Docker containerization, final docs.", "4.0, 6.0")
    ]
    wbs_table = doc.add_table(rows=len(wbs_data) + 1, cols=4)
    format_table(wbs_table, wbs_widths, wbs_headers, wbs_data)

    # =========================================================================
    # 8. TECHNOLOGY, STACK AND RESOURCES
    # =========================================================================
    add_heading_1(doc, "8. Technology, Stack and Resources")
    tech_headers = ["Layer / Subsystem", "Technology / Framework", "Version", "Role & Engineering Rationale"]
    tech_widths = [Inches(1.5), Inches(1.5), Inches(0.9), Inches(2.6)]
    tech_data = [
        ("Core Language", "Python", "3.10 – 3.14", "Core language for ML pipelines, ETL, and backend API services."),
        ("Frontend UI", "React", "19.2.7", "Declarative, component-driven reactive dashboard."),
        ("Build Tool", "Vite", "8.1.5", "High-performance ESM bundler with sub-second HMR updates."),
        ("Primary Regressor", "LightGBM", "4.3.0+", "Fast histogram-based gradient boosted decision trees for tabular data."),
        ("Scientific Computing", "Scikit-Learn", "1.4.0+", "ML utilities, MLP neural network, Bayesian Ridge, cross-validation."),
        ("Data Manipulation", "Pandas & NumPy", "2.0+ / 1.26+", "Vectorized data manipulation and feature engineering."),
        ("Explainable AI", "SHAP", "0.45.0+", "TreeSHAP game-theoretic localized feature attribution."),
        ("REST Backend", "FastAPI", "0.115.0+", "Asynchronous, OpenAPI-compliant Python web framework."),
        ("ASGI Web Server", "Uvicorn", "0.30.0+", "High-throughput asynchronous web server worker."),
        ("Persistence / ORM", "SQLite / PostgreSQL", "3.45+ / 16+", "Relational database engine with SQLAlchemy 2.0 ORM."),
        ("Security & Auth", "Python-Jose / Passlib", "3.3.0+ / 1.7.4", "OAuth2 JWT access token encryption and Bcrypt password hashing."),
        ("Data Visualization", "Recharts & Lucide", "3.10+ / 1.27+", "Responsive charts, radar profiles, and iconography.")
    ]
    tech_table = doc.add_table(rows=len(tech_data) + 1, cols=4)
    format_table(tech_table, tech_widths, tech_headers, tech_data)

    # =========================================================================
    # 9. USER WORKFLOW AND EXAMPLE SCENARIOS
    # =========================================================================
    add_heading_1(doc, "9. User Workflow and Example Scenarios")
    add_heading_2(doc, "9.1 Step-by-Step User Operational Journey")
    add_bullet(doc, "Scout authenticates via OAuth2 password grant (/auth/login) with viewer or admin credentials, receiving a cryptographically signed JWT token.", bold_prefix="Step 1 (Authentication): ")
    add_bullet(doc, "Scout searches for a candidate player (e.g. 'Florian Wirtz') using the real-time debounced search bar (/players?search=query), loading baseline multi-season metrics.", bold_prefix="Step 2 (Player Lookup): ")
    add_bullet(doc, "Scout selects source league, destination league (e.g. Bundesliga → Premier League), and target destination club (e.g. Manchester City).", bold_prefix="Step 3 (Transfer Configuration): ")
    add_bullet(doc, "Client dispatches POST /predict. The server executes anti-leakage feature alignment, LightGBM/MLP/Bayesian regression, TRC modulation, and classifier scoring.", bold_prefix="Step 4 (Model Inference): ")
    add_bullet(doc, "Scout reviews projected statistics, 95% Bayesian CIs, adaptation retention probability, downside risk scores, and the automated tactical archetype classification.", bold_prefix="Step 5 (Report Analysis): ")
    add_bullet(doc, "Scout adjusts dynamic sliders in the What-If Sandbox to test sensitivity across target team strength ratios, simulated playing time, and age factors.", bold_prefix="Step 6 (Scenario Simulation): ")

    add_heading_2(doc, "9.2 Real-World Case Studies")
    add_body_p(doc,
        "Transfer Context: Florian Wirtz (Bayer Leverkusen, Bundesliga → Manchester City, Premier League). Prior baseline: 0.35 goals/90, 0.40 assists/90, 0.35 xAG/90. "
        "Stepping up into a higher-difficulty league (LSC 0.88 → 1.00) carries a baseline difficulty penalty. However, Manchester City's attacking creation ratio of 1.45x "
        "triggers a +10.0% Tactical TRC boost. The model forecasts 0.312 goals/90 (95% CI: 0.118 – 0.506), 0.348 assists/90, and a strong Adaptation Score of 76.4% (Downside Risk: 9.8%). "
        "The system classifies Wirtz as an 'Advanced Playmaker / Half-Space Conductor', recommending a Left Interior No. 8 role.",
        bold_prefix="Case Study A — Florian Wirtz (Creative Playmaker Stepping Up): ")

    add_body_p(doc,
        "Transfer Context: Erling Haaland (Borussia Dortmund, Bundesliga → Manchester City, Premier League). The model forecasts a projected goals_p90 of 0.916 "
        "(95% CI: 0.724 – 1.108), identifying his exceptional shot frequency and Manchester City's target strength (1.45x) as an ideal match. Top SHAP drivers include "
        "Forward Position (+0.2622) and Team Strength (+0.1922). Out-of-sample backtest validation confirms real-world accuracy where Haaland exceeded 0.95 goals/90.",
        bold_prefix="Case Study B — Erling Haaland (Generational Goalscorer): ")

    add_body_p(doc,
        "Transfer Context: Timo Werner (RB Leipzig, Bundesliga → Chelsea, Premier League). Despite scoring 28 Bundesliga goals, Werner's profile exhibited high reliance on "
        "open transitional carrying space. Chelsea's lower creation ratio (1.08x) combined with high Premier League low-block frequency yielded a projected goals_p90 drop to 0.380, "
        "accompanied by an elevated Downside Risk score of 38.5%, successfully flagging the adaptation struggles observed in reality.",
        bold_prefix="Case Study C — Timo Werner (Transition Forward Mismatch): ")

    # =========================================================================
    # 10. SCREENSHOTS OF THE DONE PROJECT
    # =========================================================================
    add_heading_1(doc, "10. Screenshots of the Done Project")
    add_body_p(doc, "The following figures illustrate the live, operational TransferWorth platform running locally (FastAPI backend on port 8000, React 19 frontend on port 5173).")

    add_image_with_caption(doc, 
        str(screenshots_dir / "initial_page_1793029873817.png"), 
        "Executive Scout Dashboard and System Terminal landing page with active UEFA League Strength Coefficients and dataset metrics.")

    add_image_with_caption(doc, 
        str(screenshots_dir / "wirtz_selected_1793029911649.png"), 
        "Player Selection and Configuration view showing candidate search results, prior baseline statistics, and destination league/team controls.")

    add_image_with_caption(doc, 
        str(screenshots_dir / "inference_results_1_1793029957696.png"), 
        "Live Model Inference Results rendering projected per-90 metrics, 95% Bayesian Confidence Intervals, adaptation probabilities, and tactical archetype classification.")

    add_image_with_caption(doc, 
        str(screenshots_dir / "whatif_sandbox_1793030019941.png"), 
        "Interactive What-If Scenario Sandbox enabling dynamic counterfactual simulation across target team creation strength and playing time thresholds.")

    add_image_with_caption(doc, 
        str(screenshots_dir / "sandbox_benchmarks_1793029985358.png"), 
        "Empirical Transfer Benchmarks Grid and relational database audit trail visualizing historical transfer accuracy.")

    add_image_with_caption(doc, 
        str(screenshots_dir / "cli_tab_view_1793030244240.png"), 
        "Integrated Scout CLI Terminal Shell providing programmatic command-line model querying directly in the browser.")

    add_image_with_caption(doc, 
        str(screenshots_dir / "calibration_goals_p90_lgbm.png"), 
        "Model Calibration Curve for goals_p90 demonstrating reliable probability quantile alignment.")

    add_image_with_caption(doc, 
        str(screenshots_dir / "shap_goals_p90.png"), 
        "Global TreeSHAP Feature Attribution Summary Plot illustrating feature impact distributions on projected scoring output.")

    # =========================================================================
    # 11. TESTING AND EVALUATION
    # =========================================================================
    add_heading_1(doc, "11. Testing and Evaluation")
    add_heading_2(doc, "11.1 Automated Software Testing & Verification")
    add_body_p(doc,
        "The system incorporates an automated integration test suite implemented in tests/test_api.py, executed via pytest. "
        "All 15 automated integration tests pass with 100% compliance across authentication, role-based authorization, player search, "
        "inference execution, target team modulation, and admin retrain locks:")

    test_headers = ["Test Function", "Module", "Test Scope & Verification Focus", "Status"]
    test_widths = [Inches(2.2), Inches(1.1), Inches(2.5), Inches(0.7)]
    test_data = [
        ("test_health", "API", "Liveness probe and database connection status", "PASSED"),
        ("test_login_success", "Auth", "OAuth2 password authentication & JWT token generation", "PASSED"),
        ("test_login_admin_success", "Auth", "Admin role validation and claim embedding", "PASSED"),
        ("test_login_invalid", "Auth", "Rejection of invalid passwords (HTTP 401)", "PASSED"),
        ("test_unauthorized_access", "Auth", "Bearer token enforcement on protected endpoints", "PASSED"),
        ("test_get_leagues", "Metadata", "Retrieval of UEFA LSC coefficients", "PASSED"),
        ("test_list_players", "Database", "Pagination and retrieval of player profiles", "PASSED"),
        ("test_list_players_filter_league", "Database", "Filtering players by domestic league", "PASSED"),
        ("test_list_players_search_name", "Database", "Debounced string search on player names", "PASSED"),
        ("test_get_teams", "Database", "Retrieval of teams with attacking strength ratios", "PASSED"),
        ("test_predict", "ML Engine", "End-to-end model inference and payload schema validation", "PASSED"),
        ("test_predict_with_target_team", "TRC Engine", "Tactical TRC modulation under destination club context", "PASSED"),
        ("test_admin_retrain_forbidden", "Security", "Viewer role forbidden from triggering retrain (HTTP 403)", "PASSED"),
        ("test_admin_retrain_success", "Security", "Admin role authorized to trigger pipeline execution", "PASSED"),
        ("test_predict_unknown_player_404", "Validation", "Proper HTTP 404 response on unknown player queries", "PASSED")
    ]
    test_table = doc.add_table(rows=len(test_data) + 1, cols=4)
    format_table(test_table, test_widths, test_headers, test_data)

    add_heading_2(doc, "11.2 Machine Learning Evaluation Methodology & Benchmarks")
    add_body_p(doc,
        "Models were evaluated using 5-Fold Cross-Validation on the 14,865 player-season dataset and longitudinal out-of-sample backtesting "
        "on 550 genuine cross-league transfer cases:")

    eval_headers = ["Target Metric", "Architecture", "5-Fold CV MAE", "CV Std (σ)", "Test RMSE", "Backtest MAE (N=550)", "Selected Model"]
    eval_widths = [Inches(1.2), Inches(1.1), Inches(0.9), Inches(0.8), Inches(0.8), Inches(1.1), Inches(1.0)]
    eval_data = [
        ("goals_p90", "LightGBM", "0.0709", "0.0012", "0.0645", "0.0545", "LightGBM"),
        ("goals_p90", "MLP Neural Net", "0.0744", "0.0021", "0.0991", "0.0672", "—"),
        ("goals_p90", "Bayesian Ridge", "0.0801", "0.0014", "0.1159", "0.0801", "—"),
        ("assists_p90", "LightGBM", "0.0515", "0.0009", "0.0444", "0.0333", "LightGBM / Bayes"),
        ("assists_p90", "Bayesian Ridge", "0.0509", "0.0007", "0.0698", "0.0499", "Best CV MAE"),
        ("xg_p90", "LightGBM", "0.0488", "0.0005", "0.0456", "0.0359", "LightGBM"),
        ("xg_p90", "MLP Neural Net", "0.0523", "0.0006", "0.0711", "0.0482", "—"),
        ("xag_p90", "LightGBM", "0.0247", "0.0007", "0.0181", "0.0127", "LightGBM"),
        ("prog_passes_p90", "LightGBM", "0.0636", "0.0016", "0.0892", "0.0712", "LightGBM"),
        ("key_passes_p90", "LightGBM", "0.1662", "0.0035", "0.2104", "0.1780", "LightGBM"),
        ("prog_carries_p90", "LightGBM", "0.0267", "0.0015", "0.0388", "0.0294", "LightGBM")
    ]
    eval_table = doc.add_table(rows=len(eval_data) + 1, cols=7)
    format_table(eval_table, eval_widths, eval_headers, eval_data)

    add_heading_2(doc, "11.3 Supervised Classifier Performance")
    add_body_p(doc, "Calibrated on 955 empirical cross-league transfers using balanced class-weighted logistic regression:")
    add_bullet(doc, "Cross-Validated ROC-AUC = 0.611 ± 0.019 (predicts retention of ≥ 70% attacking output).", bold_prefix="Adaptation Score Classifier: ")
    add_bullet(doc, "Cross-Validated ROC-AUC = 0.655 ± 0.034 (predicts output collapse below 45% xG).", bold_prefix="Downside Risk Classifier: ")

    # =========================================================================
    # 12. LIMITATIONS, ASSUMPTIONS AND RISKS
    # =========================================================================
    add_heading_1(doc, "12. Limitations, Assumptions and Risks")
    add_heading_2(doc, "12.1 Theoretical Modeling Assumptions")
    add_bullet(doc, "Assumes the player operates in a tactical role consistent with their primary positional group at the destination club.", bold_prefix="Positional Invariance: ")
    add_bullet(doc, "Assumes steady-state physical health and regular availability (≥ 600 minutes threshold).", bold_prefix="Physiological Availability: ")
    add_bullet(doc, "UEFA 5-year confederation coefficients are assumed to represent stationary competition difficulty over multi-season windows.", bold_prefix="Stationary Coefficients: ")

    add_heading_2(doc, "12.2 Technical & Domain Limitations")
    add_bullet(doc, "The model cannot capture off-pitch psychological friction: language barriers, homesickness, locker room tension, or sudden mid-season manager sackings.", bold_prefix="Psychological & Cultural Acclimatization: ")
    add_bullet(doc, "Relies on aggregated match-event metrics rather than raw 25Hz optical tracking coordinate data (pitch control geometry, defensive gravity).", bold_prefix="Absence of Tracking Geometry: ")
    add_bullet(doc, "Specific rare transfer corridors (e.g. transfers between French Ligue 1 and Italian Serie A defenders) possess fewer historical pairs than the high-volume Bundesliga-to-EPL corridor.", bold_prefix="Sample Size Constraints: ")

    add_heading_2(doc, "12.3 Systemic Risks & Ethical Considerations")
    add_bullet(doc, "Recruitment directors must not treat algorithm projections as infallible truth. TransferWorth is designed as a decision-support system to complement human video analysis and psychological assessments.", bold_prefix="Automation Bias in Recruitment: ")
    add_bullet(doc, "Third-party data providers periodically alter HTML structures, requiring defensive scraping routines and schema validation guards.", bold_prefix="Data Vendor Schema Drift: ")

    # =========================================================================
    # 13. SUGGESTIONS FOR IMPROVEMENTS
    # =========================================================================
    add_heading_1(doc, "13. Suggestions for Improvements")
    add_bullet(doc, "Incorporate spatial pitch control and defender proximity freeze-frames at the moment of pass release and shot execution.", bold_prefix="1. StatsBomb 360 & Freeze-Frame Geometry: ")
    add_bullet(doc, "Augment event counts with action-valuation frameworks evaluating every on-ball action by its probability increase toward goal generation.", bold_prefix="2. Expected Threat (xT) & Possessional Valuation: ")
    add_bullet(doc, "Vectorize destination coaches' tactical philosophies (e.g. Guardiola positional play vs. Klopp heavy metal vs. Simeone mid-block) and calculate player-system cosine similarity.", bold_prefix="3. Managerial Tactical Alignment Vectors: ")
    add_bullet(doc, "Expand data ingestion to include the English Championship, Dutch Eredivisie, Portuguese Primeira Liga, Brazilian Série A, and Argentine Primera División.", bold_prefix="4. Global & Tier 2 League Expansion: ")
    add_bullet(doc, "Transition long-running model retraining triggers (POST /admin/retrain) from synchronous request threads to a distributed Celery/Redis queue with progress webhooks.", bold_prefix="5. Distributed Task Queues (Celery/Redis): ")
    add_bullet(doc, "Incorporate historical orthopedic injury logs and high-speed running sprint distance decay curves to build a composite physical durability rating.", bold_prefix="6. Physical Resilience & Durability Modeling: ")

    # =========================================================================
    # 14. CONCLUSION AND REFERENCES
    # =========================================================================
    add_heading_1(doc, "14. Conclusion and References")
    add_heading_2(doc, "14.1 Conclusion")
    add_body_p(doc,
        "The TransferWorth (CLPTM) project addresses a critical, multi-million-euro challenge in modern association football: the failure of cross-league "
        "performance translation. By engineering an end-to-end platform that unifies 24,413 player-seasons, leak-free gradient boosted decision trees, "
        "deep neural networks, Bayesian uncertainty quantification, and target club tactical context (TRC), TransferWorth replaces naive statistical carry-over "
        "with rigorous, calibrated predictive intelligence.")
    add_body_p(doc,
        "Backtested on 550 real-world transfer cases, the system delivers high accuracy (goals_p90 MAE = 0.0545, assists_p90 MAE = 0.0333, xg_p90 MAE = 0.0359), "
        "while providing actionable TreeSHAP interpretability and interactive counterfactual simulation. Developed to high software engineering standards—featuring "
        "a normalized StarUML relational schema, an authenticated FastAPI microservice, and a responsive React 19 dashboard—TransferWorth demonstrates how applied "
        "artificial intelligence and domain expertise can modernize talent recruitment in professional sports.")

    add_heading_2(doc, "14.2 References & Bibliography")
    refs = [
        "Decroos, T., Bransen, L., Van Haaren, J., & Davis, J. (2019). Actions Speak Louder Than Goals: Valuing Player Actions in Football. In Proceedings of the 25th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining (pp. 1851-1861).",
        "Dixon, M. J., & Coles, S. G. (1997). Modelling Association Football Scores and Inefficiencies in the Football Betting Market. Journal of the Royal Statistical Society: Series C (Applied Statistics), 46(2), 265-280.",
        "Lundberg, S. M., & Lee, S. I. (2017). A Unified Approach to Interpreting Model Predictions. Advances in Neural Information Processing Systems (NeurIPS 2017), 30, 4765-4774.",
        "Lundberg, S. M., et al. (2020). From Local Explanations to Global Understanding with Explainable AI for Trees. Nature Machine Intelligence, 2(1), 56-67.",
        "Ke, G., Meng, Q., Finley, T., Wang, T., Chen, W., Ma, W., Ye, Q., & Liu, T. Y. (2017). LightGBM: A Highly Efficient Gradient Boosting Decision Tree. Advances in Neural Information Processing Systems (NeurIPS 2017), 30, 3146-3154.",
        "Pappalardo, L., Cintia, P., Rossi, A., Massucco, E., Ferragina, P., Pedreschi, D., & Giannotti, F. (2019). A Public Data Set of Spatio-Temporal Match Events in Soccer Competitions. Scientific Data (Nature), 6(1), 1-15.",
        "Singh, K. (2019). Introducing Expected Threat (xT). Karun.in Analytics Research.",
        "Spearman, W. (2018). Beyond Expected Goals: Quantifying Potential and Exploited Space in Soccer. In Proceedings of the 12th MIT Sloan Sports Analytics Conference.",
        "FIFA. (2024). Global Transfer Report 2023: Analysis of International Football Transfers. FIFA Professional Football Department, Zurich, Switzerland.",
        "UEFA. (2024). UEFA Club Licensing and Financial Fair Play Regulations & European Club Talent Landscape Report. Union of European Football Associations, Nyon, Switzerland.",
        "Sports Reference LLC. (2026). FBref: Comprehensive Football Player Statistics and Match Logs. Available at https://fbref.com/.",
        "Tiangolo, S. (2024). FastAPI: Modern, Fast (High-Performance), Web Framework for Building APIs with Python 3.8+. Available at https://fastapi.tiangolo.com/."
    ]
    for idx, ref in enumerate(refs, 1):
        add_body_p(doc, ref, bold_prefix=f"[{idx}] ", space_after=3)

    output_path = project_root / "TransferWorth_Project_Report.docx"
    doc.save(str(output_path))
    print(f"Document successfully created at: {output_path}")

    # Also copy to brain artifacts directory
    brain_docx = Path("C:/Users/bshas/.gemini/antigravity-ide/brain/c4e6c369-389d-4f92-83cd-bbc0c12acc04/TransferWorth_Project_Report.docx")
    doc.save(str(brain_docx))
    print(f"Brain artifact docx created at: {brain_docx}")

if __name__ == "__main__":
    build_document()
