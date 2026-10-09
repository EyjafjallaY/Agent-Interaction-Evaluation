"""Forest plots colored by the exported correction and fit diagnostic fields."""
import numpy as np


def forest_plot(table, destination, title, synthetic=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    table = table.copy().reset_index(drop=True)
    needed = {"beta","CI95_low","CI95_high","p_adjusted","significant_usable", "fit_review_required"}
    if not needed.issubset(table):
        raise ValueError("Plot requires adjusted p-values and fit diagnostics")
    fig, ax = plt.subplots(figsize=(10, max(3, .32*len(table)+1.5)))
    labels = []
    for i, row in table.iterrows():
        label = f"P{int(row.Original_Phase)} / {row.DV}"
        if "Trait" in table:
            label += f" / {row.Trait} / {row.Effect}"
        if row.fit_review_required:
            label += " [review fit]"
        labels.append(label)
        if np.isfinite([row.beta,row.CI95_low,row.CI95_high]).all():
            color = "#b42318" if row.significant_usable else "#374151"
            ax.plot([row.CI95_low,row.CI95_high],[i,i],color=color,lw=1.4)
            ax.plot(row.beta,i,"o",color=color,mfc="white" if row.fit_review_required else color,ms=5)
    ax.axvline(0,color="#9ca3af",ls="--",lw=1)
    ax.set_yticks(range(len(labels)),labels,fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Fixed-effect estimate with unadjusted 95% Wald CI")
    ax.set_title(title + ("\nSynthetic demonstration" if synthetic else "\nArchived notebook analysis profile"),fontsize=11)
    ax.spines[["top","right"]].set_visible(False)
    fig.text(.02,.015,"Red: adjusted p < .05 and no fit warning. Hollow: inspect fit diagnostics.",fontsize=8)
    fig.tight_layout(rect=(0,.04,1,1))
    fig.savefig(destination,dpi=160)
    plt.close(fig)
