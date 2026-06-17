"""Generate sample research paper PDFs for testing the AI Scientist app."""
import fitz  # PyMuPDF

PAPERS = [
    {
        "filename": "transformer_attention_mechanisms.pdf",
        "title": "Advances in Transformer Attention Mechanisms for Long-Context Reasoning",
        "authors": "Sarah Chen, Michael Patel, Yuki Tanaka",
        "abstract": (
            "Transformer models have revolutionized natural language processing, yet their quadratic "
            "attention complexity limits scalability to long contexts. In this paper, we survey recent "
            "advances including sparse attention, linear attention approximations, and sliding window "
            "approaches. We demonstrate that existing methods reduce memory usage but introduce "
            "trade-offs in retrieval accuracy for distant tokens. Our experiments on long-document "
            "benchmarks reveal a persistent accuracy gap of 12-18% compared to full attention, "
            "particularly for multi-hop reasoning tasks. We identify cross-segment dependency modeling "
            "as an underexplored area with significant potential for improvement."
        ),
        "sections": [
            ("1. Introduction",
             "Large language models (LLMs) based on the Transformer architecture have achieved "
             "state-of-the-art performance across diverse NLP tasks. The self-attention mechanism "
             "is central to their success, allowing each token to attend to every other token in "
             "the sequence. However, this full attention has O(n^2) complexity in sequence length n, "
             "making it prohibitively expensive for contexts exceeding 4,096 tokens.\n\n"
             "Recent work has explored several families of efficient attention: (1) sparse patterns "
             "that restrict which tokens can attend to each other, (2) low-rank approximations that "
             "project keys and values to a smaller dimension, and (3) hierarchical approaches that "
             "process text in chunks. Despite progress, a unified understanding of when each approach "
             "works best remains elusive."),
            ("2. Background",
             "The standard self-attention computes Q = XW_Q, K = XW_K, V = XW_V and outputs "
             "Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) V. For a sequence of length n and "
             "head dimension d_k, this requires O(n^2 d_k) time and O(n^2) memory.\n\n"
             "Longformer (Beltagy et al., 2020) introduced local windowed attention combined with "
             "global tokens. BigBird (Zaheer et al., 2020) added random attention to the local + "
             "global pattern. Performer (Choromanski et al., 2021) used random feature maps to "
             "approximate the softmax kernel in linear time. Flash Attention (Dao et al., 2022) "
             "achieved exact attention with IO-aware tiling, reducing memory from O(n^2) to O(n)."),
            ("3. Experimental Setup",
             "We evaluate seven efficient attention methods on three benchmarks: SCROLLS (long "
             "document summarization), QuALITY (multiple-choice reading comprehension), and HotpotQA "
             "(multi-hop question answering). All models use a 1B parameter base trained on The Pile "
             "and fine-tuned for 10k steps on each task.\n\n"
             "Sequence lengths range from 4k to 32k tokens. We report accuracy, memory peak (GB), "
             "and throughput (tokens/sec). Experiments run on 8x A100 80GB GPUs. Hyperparameters are "
             "swept over learning rate in {1e-5, 3e-5, 1e-4} and window size in {256, 512, 1024}."),
            ("4. Results",
             "Full attention achieves 84.3% on QuALITY at 4k context. At 16k context, accuracy drops "
             "to 79.1% while memory increases 16x. Sparse methods maintain 76-78% accuracy with only "
             "2-3x memory increase, but degrade to 61-65% on multi-hop tasks requiring cross-segment "
             "reasoning.\n\n"
             "Linear attention methods (Performer, cosFormer) show the steepest accuracy drop at 12k+ "
             "tokens, suggesting the softmax approximation loses critical information for long-range "
             "dependencies. Flash Attention matches full attention exactly while cutting memory 4x, "
             "but does not address the fundamental O(n^2) compute cost.\n\n"
             "We observe an accuracy gap of 12-18% on HotpotQA that no current efficient method closes, "
             "particularly when supporting evidence spans are more than 8k tokens apart."),
            ("5. Discussion and Open Problems",
             "Our analysis reveals three underexplored research directions. First, current sparse "
             "patterns are fixed at training time; dynamic routing of attention based on content "
             "could improve retrieval of relevant distant context. Second, all evaluated methods "
             "treat all layers identically — layer-wise adaptation of attention span may yield gains. "
             "Third, the interaction between positional encodings and efficient attention is poorly "
             "understood; RoPE and ALiBi behave differently under sparse masking.\n\n"
             "A particularly promising but unstudied approach is cross-segment memory banks that "
             "compress prior context into fixed-size representations, allowing O(n) attention while "
             "preserving semantic information from arbitrary distances."),
            ("6. Conclusion",
             "Efficient attention mechanisms have made Transformers practical for longer contexts, "
             "but a significant accuracy gap remains for tasks requiring long-range multi-hop reasoning. "
             "We call for research into dynamic attention routing, layer-adaptive span selection, and "
             "compressed cross-segment memory as promising directions to close this gap."),
            ("References",
             "Beltagy I., Peters M.E., Cohan A. (2020). Longformer: The Long-Document Transformer. arXiv:2004.05150.\n"
             "Choromanski K. et al. (2021). Rethinking Attention with Performers. ICLR 2021.\n"
             "Dao T. et al. (2022). FlashAttention: Fast and Memory-Efficient Exact Attention. NeurIPS 2022.\n"
             "Vaswani A. et al. (2017). Attention Is All You Need. NeurIPS 2017.\n"
             "Zaheer M. et al. (2020). Big Bird: Transformers for Longer Sequences. NeurIPS 2020."),
        ],
    },
    {
        "filename": "protein_folding_drug_discovery.pdf",
        "title": "Leveraging AlphaFold2 Predictions for Structure-Based Drug Discovery: Opportunities and Limitations",
        "authors": "Elena Rodriguez, James Wu, Priya Sharma, Thomas Beck",
        "abstract": (
            "AlphaFold2 has dramatically expanded the structural coverage of the human proteome, "
            "enabling structure-based drug discovery for previously undruggable targets. We analyze "
            "1,247 AlphaFold2 structures of disease-relevant proteins and assess their utility for "
            "virtual screening campaigns. While high-confidence regions (pLDDT > 90) show docking "
            "performance comparable to experimental structures, low-confidence disordered regions and "
            "holo-form prediction remain significant challenges. We identify 89 cryptic binding sites "
            "predicted by AlphaFold2 that are absent in available crystal structures, suggesting new "
            "druggable opportunities. The conformational flexibility required for induced-fit docking "
            "in these sites remains an open problem."
        ),
        "sections": [
            ("1. Introduction",
             "Drug discovery typically requires high-resolution 3D protein structures to enable "
             "rational design of small molecule inhibitors. Historically, structural data has been "
             "available for only ~30% of human proteins with therapeutic relevance. The 2021 release "
             "of AlphaFold2 (Jumper et al., 2021) and its subsequent database covering 200M+ proteins "
             "represents a paradigm shift, providing predicted structures for virtually every protein "
             "in the human proteome.\n\n"
             "However, critical questions remain about the reliability of these predictions for drug "
             "discovery. Predicted structures represent apo-form (ligand-free) conformations, whereas "
             "binding sites often undergo conformational changes upon ligand binding (induced fit). "
             "Additionally, intrinsically disordered regions, which are common in transcription factors "
             "and signaling proteins, receive low confidence scores and may not represent meaningful "
             "binding geometries."),
            ("2. Methods",
             "We downloaded AlphaFold2 structures for 1,247 proteins linked to OMIM disease entries "
             "with no existing approved drugs. Structures were processed using Schrödinger's Protein "
             "Preparation Wizard. Binding site prediction used FPocket 4.0 and SiteMap.\n\n"
             "For validation, we compared AlphaFold2-based docking (Glide SP) against experimental "
             "crystal structure docking for 203 proteins with both available. Ligand libraries included "
             "ZINC15 (2M drug-like compounds) and FDA-approved drugs (2,650 compounds). Docking "
             "accuracy was assessed by re-docking known co-crystallized ligands and measuring RMSD."),
            ("3. Binding Site Analysis",
             "Among 1,247 analyzed proteins, 847 (67.9%) had at least one predicted binding pocket "
             "with SiteScore > 0.8. Of these, 89 proteins showed cryptic sites — pockets present in "
             "the AlphaFold2 structure but absent in all available PDB entries for that protein. "
             "Cryptic sites were enriched in protein-protein interaction interfaces (41%) and allosteric "
             "regions (33%).\n\n"
             "High-confidence regions (pLDDT > 90) covering predicted binding sites correlated strongly "
             "with experimental binding site geometry (RMSD < 1.5 Å in 78% of cases). Low-confidence "
             "regions (pLDDT < 70) showed poor geometry preservation, with 61% having RMSD > 3 Å."),
            ("4. Virtual Screening Performance",
             "Re-docking of co-crystallized ligands into AlphaFold2 structures achieved < 2 Å RMSD "
             "in 71% of cases for high-confidence binding sites, compared to 84% for experimental "
             "structures. For kinases, performance was near-equivalent (79% vs 82%). For GPCRs, "
             "performance dropped sharply (52% vs 77%), likely due to transmembrane helix flexibility.\n\n"
             "Prospective virtual screening of the FDA drug library against 50 novel targets identified "
             "131 candidate interactions. Of 24 experimentally tested, 9 (37.5%) showed binding affinity "
             "Kd < 10 μM, validating AlphaFold2-based screening as a useful but imperfect filter.\n\n"
             "Notably, allosteric sites in transcription factors showed the lowest hit rates (2/11 = 18%), "
             "highlighting the need for ensemble docking approaches that sample multiple conformations."),
            ("5. Open Challenges",
             "Several critical gaps limit the current utility of AlphaFold2 for drug discovery. "
             "First, induced-fit modeling remains computationally expensive and not routinely applicable "
             "at proteome scale. Second, prediction of protein-ligand co-complexes (holo structures) "
             "is an unsolved problem; recent methods like RoseTTAFold All-Atom show promise but "
             "have not been benchmarked at scale.\n\n"
             "Third, post-translational modifications (phosphorylation, ubiquitination) that alter "
             "binding site geometry are not captured. Fourth, protein dynamics — especially loop "
             "flexibility in active sites — requires molecular dynamics simulation that does not "
             "scale to proteome-wide analysis. Integrating MD-generated conformational ensembles "
             "with deep learning binding prediction represents a major open research direction."),
            ("6. Conclusion",
             "AlphaFold2 structures are broadly useful for structure-based drug discovery, particularly "
             "for high-confidence globular domains. The 89 cryptic sites identified in this work "
             "represent novel therapeutic opportunities. Closing the performance gap for flexible, "
             "disordered, and allosteric targets will require advances in conformational ensemble "
             "generation and induced-fit docking at scale."),
            ("References",
             "Jumper J. et al. (2021). Highly accurate protein structure prediction with AlphaFold. Nature 596.\n"
             "Friesner R.A. et al. (2004). Glide: A New Approach for Rapid, Accurate Docking. J. Med. Chem.\n"
             "Le Guilloux V. et al. (2009). Fpocket: An open source platform for ligand pocket detection. BMC Bioinformatics.\n"
             "Baek M. et al. (2021). Accurate prediction of protein structures and interactions using RoseTTAFold. Science.\n"
             "Binder J.L. et al. (2022). AlphaFold illuminates half of the dark human proteome. Nat. Struct. Mol. Biol."),
        ],
    },
    {
        "filename": "climate_ml_carbon_prediction.pdf",
        "title": "Machine Learning Approaches for Regional Carbon Flux Prediction: A Systematic Review",
        "authors": "Marcus Johnson, Aisha Okonkwo, Lars Eriksson",
        "abstract": (
            "Accurate prediction of regional carbon fluxes is critical for climate mitigation policy, "
            "yet current process-based models carry large uncertainties. We review 84 studies applying "
            "machine learning to carbon flux estimation from 2015-2024, covering eddy covariance, "
            "satellite remote sensing, and atmospheric inversion datasets. Deep learning methods "
            "outperform traditional models by 23% on held-out test sets, but exhibit poor "
            "generalization across biomes and climate regimes not seen during training. We find that "
            "soil carbon dynamics, permafrost feedback, and extreme weather events are systematically "
            "underrepresented in training data, creating dangerous blind spots for climate projections "
            "beyond 2050. We propose a hybrid physical-ML framework as a path toward generalizable "
            "carbon cycle modeling."
        ),
        "sections": [
            ("1. Introduction",
             "The global carbon cycle determines the pace of climate change. Terrestrial ecosystems "
             "absorb approximately 30% of annual anthropogenic CO2 emissions, but this land carbon "
             "sink shows high interannual variability driven by temperature, precipitation, and "
             "disturbance regimes. Process-based land surface models (LSMs) disagree by up to 2 PgC/yr "
             "in their estimates of the tropical carbon balance, limiting confidence in climate projections.\n\n"
             "Machine learning offers an alternative data-driven approach that can leverage the "
             "explosion of Earth observation data: eddy covariance flux towers (FLUXNET, 200+ sites), "
             "MODIS/VIIRS satellite products, and atmospheric CO2 from OCO-2/3. However, the "
             "data-driven paradigm raises fundamental questions about out-of-distribution generalization "
             "and physical consistency that have not been systematically addressed."),
            ("2. Review Methodology",
             "We searched Web of Science and Scopus for studies combining machine learning with carbon "
             "flux estimation, published January 2015 – June 2024. Inclusion criteria: (1) quantitative "
             "comparison with a baseline model, (2) evaluation on held-out temporal or spatial data, "
             "(3) focus on net ecosystem exchange (NEE), gross primary production (GPP), or soil "
             "respiration (Rs). After screening, 84 studies met criteria.\n\n"
             "Studies were categorized by: ML method (random forest, gradient boosting, LSTM, CNN, "
             "transformer), input data source (in-situ, satellite, reanalysis), spatial scale (site, "
             "regional, global), and validation approach (temporal split, spatial cross-validation, "
             "leave-one-site-out)."),
            ("3. Performance Analysis",
             "Across all 84 studies, deep learning methods (LSTM, transformer, CNN) outperformed "
             "random forest and gradient boosting by 23% mean RMSE reduction on held-out test sets. "
             "Transformers showed the strongest performance for multi-site generalization (R^2 = 0.87 "
             "vs 0.79 for LSTM) likely due to their ability to model long-range temporal dependencies.\n\n"
             "However, performance degrades sharply under spatial cross-validation: models trained on "
             "temperate forests predict tropical forest fluxes with R^2 = 0.31, compared to R^2 = 0.84 "
             "in-distribution. Arctic and boreal sites show the worst out-of-distribution performance "
             "(R^2 = 0.19), despite being critical for understanding permafrost carbon feedbacks.\n\n"
             "Only 12 of 84 studies reported performance under climate extremes (drought, heatwave). "
             "In these studies, ML model error increased 2.8x during extreme events compared to "
             "baseline conditions, suggesting models have not learned the mechanisms driving flux "
             "anomalies under novel climate forcing."),
            ("4. Data Gaps and Blind Spots",
             "Three systematic gaps in training data limit current ML carbon models. First, soil carbon "
             "dynamics: only 8% of studies included deep soil carbon (>30 cm) measurements, yet "
             "permafrost soils store ~1,500 PgC — roughly double the current atmospheric carbon stock. "
             "Second, extreme events: FLUXNET tower coverage of drought years is sparse and biased "
             "toward European sites, limiting generalization to tropical and monsoon systems.\n\n"
             "Third, disturbance regimes: fire, insect outbreaks, and logging create large transient "
             "carbon fluxes poorly captured by satellite indices. Post-disturbance recovery trajectories "
             "lasting decades are absent from most training datasets, leading models to systematically "
             "underestimate forest regrowth carbon uptake by 15-40% in remote sensing studies.\n\n"
             "We identify a critical need for targeted data collection in data-sparse high-impact "
             "regions: the Congo Basin, Siberian larch forests, and South American cerrado."),
            ("5. Toward Hybrid Physical-ML Models",
             "Pure data-driven models lack the physical constraints needed for reliable extrapolation "
             "to future climate states. We propose a hybrid framework: use ML to learn residuals of "
             "a process-based LSM, constrained to conserve mass and energy. This approach, tested in "
             "3 studies reviewed, achieves 18% lower RMSE than either the LSM or ML alone while "
             "maintaining physical plausibility.\n\n"
             "Key open problems for hybrid models include: (1) differentiable LSM implementations "
             "that allow gradient-based training, (2) uncertainty quantification that propagates "
             "both model and observation uncertainty, (3) multi-objective training that balances "
             "predictive accuracy with physical constraint satisfaction. Neural ODEs and physics-informed "
             "neural networks represent promising architectures not yet applied to carbon cycle modeling."),
            ("6. Conclusion",
             "Machine learning has substantially improved carbon flux prediction accuracy, but "
             "generalization across biomes and climate regimes remains poor. The systematic underrepresentation "
             "of permafrost, disturbance, and extreme events in training data poses risks for climate "
             "projections. Hybrid physical-ML architectures, combined with targeted data collection "
             "in underrepresented ecosystems, offer the most promising path toward reliable global "
             "carbon cycle modeling."),
            ("References",
             "Jung M. et al. (2020). Scaling carbon fluxes from eddy covariance sites to globe. Biogeosciences.\n"
             "Reichstein M. et al. (2019). Deep learning and process understanding for data-driven Earth system science. Nature.\n"
             "Tramontana G. et al. (2016). Predicting carbon dioxide and energy fluxes across global FLUXNET sites. Biogeosciences.\n"
             "Zhu X.J. et al. (2016). What is the optimum climate for global soil carbon stocks? Scientific Reports.\n"
             "Seneviratne S.I. et al. (2012). Changes in climate extremes and their impacts on the natural physical environment. IPCC."),
        ],
    },
]


def make_pdf(paper: dict, output_path: str):
    doc = fitz.open()
    page_width, page_height = 595, 842  # A4

    margin_x = 72
    margin_top = 72
    margin_bottom = 60
    text_width = page_width - 2 * margin_x

    def new_page():
        p = doc.new_page(width=page_width, height=page_height)
        return p, margin_top

    def insert_wrapped(page, y, text, fontsize, bold=False, line_height_factor=1.4, color=(0, 0, 0)):
        fontname = "helv" if not bold else "hebo"
        line_height = fontsize * line_height_factor
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if fitz.get_text_length(test, fontname=fontname, fontsize=fontsize) <= text_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        for line in lines:
            if y + line_height > page_height - margin_bottom:
                page, y = new_page()
                pages.append(page)
            page.insert_text(
                (margin_x, y),
                line,
                fontname=fontname,
                fontsize=fontsize,
                color=color,
            )
            y += line_height
        return page, y

    pages = []
    page, y = new_page()
    pages.append(page)

    # Title
    page, y = insert_wrapped(page, y, paper["title"], fontsize=16, bold=True, line_height_factor=1.5)
    y += 8

    # Authors
    page, y = insert_wrapped(page, y, paper["authors"], fontsize=10, color=(0.3, 0.3, 0.3))
    y += 16

    # Horizontal rule (simulate with a rectangle)
    page.draw_line((margin_x, y), (page_width - margin_x, y), color=(0.7, 0.7, 0.7), width=0.5)
    y += 14

    # Abstract
    page, y = insert_wrapped(page, y, "Abstract", fontsize=11, bold=True)
    y += 4
    page, y = insert_wrapped(page, y, paper["abstract"], fontsize=9.5, line_height_factor=1.5, color=(0.15, 0.15, 0.15))
    y += 20

    page.draw_line((margin_x, y), (page_width - margin_x, y), color=(0.7, 0.7, 0.7), width=0.5)
    y += 14

    # Sections
    for heading, body in paper["sections"]:
        if y > page_height - 150:
            page, y = new_page()
            pages.append(page)

        page, y = insert_wrapped(page, y, heading, fontsize=11, bold=True, color=(0.05, 0.05, 0.4))
        y += 5
        for para in body.split("\n\n"):
            para = para.strip()
            if para:
                page, y = insert_wrapped(page, y, para, fontsize=9.5, line_height_factor=1.55, color=(0.1, 0.1, 0.1))
                y += 8
        y += 10

    doc.save(output_path)
    doc.close()
    print(f"  Created: {output_path}")


if __name__ == "__main__":
    import os
    out_dir = os.path.dirname(os.path.abspath(__file__))
    for paper in PAPERS:
        make_pdf(paper, os.path.join(out_dir, paper["filename"]))
    print("Done. 3 sample PDFs ready.")
