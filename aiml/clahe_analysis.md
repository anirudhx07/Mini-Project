# CLAHE Quantitative Performance Analysis

## Per-Image IoU Comparison Table

| Image | Plain IoU | CLAHE 1.0 IoU | CLAHE 2.0 IoU | CLAHE 4.0 IoU | Change (2.0 vs Plain) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `camourflage_00012.jpg` | `0.8173` | `0.8113` | `0.7965` | `0.7828` | `-0.0208` |
| `camourflage_00018.jpg` | `0.5449` | `0.5977` | `0.6213` | `0.5067` | `+0.0764` |
| `camourflage_00061.jpg` | `0.7321` | `0.7374` | `0.7879` | `0.7538` | `+0.0558` |
| `camourflage_00064.jpg` | `0.2871` | `0.1512` | `0.0737` | `0.0880` | `-0.2134` |
| `camourflage_00071.jpg` | `0.2788` | `0.2327` | `0.2210` | `0.1447` | `-0.0578` |
| `camourflage_00079.jpg` | `0.8663` | `0.8713` | `0.8754` | `0.8532` | `+0.0091` |
| `camourflage_00087.jpg` | `0.7758` | `0.7999` | `0.8094` | `0.7876` | `+0.0336` |
| `camourflage_00088.jpg` | `0.4917` | `0.5090` | `0.4809` | `0.4617` | `-0.0108` |
| `camourflage_00090.jpg` | `0.6172` | `0.7324` | `0.7482` | `0.7391` | `+0.1310` |
| `camourflage_00097.jpg` | `0.5831` | `0.6564` | `0.8605` | `0.8502` | `+0.2774` |
| `camourflage_00098.jpg` | `0.8125` | `0.8246` | `0.8305` | `0.8507` | `+0.0180` |
| `camourflage_00100.jpg` | `0.3741` | `0.4403` | `0.4845` | `0.4867` | `+0.1104` |

## Statistical Summary (CLAHE clipLimit 2.0 vs Plain, Tolerance = 0.01)

- **Total Images Evaluated**: 12
- **Images Improved (change > +0.01)**: 7 of 12 (58.3%)
- **Images Got Worse (change < -0.01)**: 4 of 12 (33.3%)
- **Images Unchanged (|change| <= 0.01)**: 1 of 12 (8.3%)
- **Mean IoU Change**: +0.0341
- **Median IoU Change**: +0.0258
- **Single Best-Improving Image**: `camourflage_00097.jpg` (gain = `+0.2774`)
- **Mean IoU Change (Excluding Best-Improving Image)**: +0.0120
