"""animate.py

Violence (ACLED) and UN peacekeeping deployments (RADPKO) in Africa by
PRIO-GRID cell, one frame per month, each frame summarizing the trailing 12
months. Shown on the site's home page (_includes/pk-animation.html).

Besides the map, the figure has:
  * a pair of aligned timelines (continent-wide fatalities and peacekeepers)
    with a moving cursor. An animation asks the reader to remember earlier
    frames; the timelines put the whole series on a common position scale so
    the current month can be compared to every other month at a glance.
  * a caption note that red and blue circles use separate size scales.

The figure is drawn on the site's page color (PAGE_BG) so it sits on the page
without a visible panel.

Run from this folder:
    python animate.py
Requires: pandas, numpy, geopandas, matplotlib, pillow, imageio-ffmpeg
(see requirements.txt).
Outputs:
    ../../images/pk_violence_tall.mp4        web video
    ../../images/pk_violence_tall.png        poster = final frame
The GIF export is commented out (the site uses the MP4). To bring it back,
uncomment the lines marked GIF and create ./output first.
"""

import glob
import textwrap

import geopandas as gpd
import imageio_ffmpeg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from PIL import Image

##### SETTINGS #####
ACLED_PATH = sorted(glob.glob("./data/acled/*.csv"))[0]
ACLED_ACCESSED = "26 Aug 2026"            # date the ACLED export was downloaded
# GIF_FILE = "./output/pk_violence_all_separate_py.gif"  # GIF
WEB_DIR = "../../images"                  # the site's images folder
PAGE_BG = "#f7f6f3"                       # the site's --paper color (splitscreen.css)
FIRST_FRAME = "2000-09"                   # first full 12 months of RADPKO (starts 1999-10)
LAST_FRAME = "2017-12"                    # RADPKO ends early 2018
FPS = 12
HOLD_SECONDS = 2                          # hold on the last frame
VIO_LABEL = "Fatalities, all event types"

RED, BLUE = "#e5695b", "#5b92e5"
INK, MUTED, FAINT = "#262626", "#595959", "#8c8c8c"

# size scales: area proportional to value, separate for each layer, fixed
# across frames. Violence is right-skewed, so its scale tops out at VIO_CAP and
# larger values are drawn at the cap (legend reads "1,000+").
VIO_CAP = 1000
VIO_BREAKS = [50, 250, 1000]
VIO_MAX_DIAM = 46                         # points, circle diameter at the cap
PK_BREAKS = [1000, 3000, 6000]
PK_MAX_DIAM = 33                          # points, circle diameter at pk max

CAPTION = ("Circles: PRIO-GRID cells (0.5°). Violence = 12-month total; peacekeepers = "
           "12-month average personnel. Circle area is proportional to value, but red "
           "and blue use separate size scales. Timelines sum all cells. Data: ACLED "
           "(Armed Conflict Location & Event Data), acleddata.com, accessed "
           f"{ACLED_ACCESSED}; RADPKO (Hunnicutt & Nomikos 2020).")

plt.rcParams.update({
    "font.family": ["Arial", "DejaVu Sans"],
    "font.size": 9,
    "axes.edgecolor": FAINT,
})


##### HELPERS #####
def month_idx(dates):
    """Months since Jan 0000, so 12-month windows are integer math."""
    d = pd.to_datetime(dates)
    return (d.dt.year * 12 + d.dt.month - 1).to_numpy()


def idx_label(i, fmt="%b %Y"):
    return pd.Timestamp(year=int(i) // 12, month=int(i) % 12 + 1, day=1).strftime(fmt)


def lonlat_gid(lon, lat):
    """PRIO-GRID id of the 0.5 degree cell containing each point."""
    return (np.floor((lat + 90) / 0.5) * 720 + np.floor((lon + 180) / 0.5) + 1).astype(int)


def gid_xy(gid):
    gid = np.asarray(gid)
    return ((gid - 1) % 720 + 0.5) * 0.5 - 180, ((gid - 1) // 720 + 0.5) * 0.5 - 90


f0 = month_idx(pd.Series([FIRST_FRAME]))[0]
f1 = month_idx(pd.Series([LAST_FRAME]))[0]
w0 = f0 - 11                              # first month in the first window
n_frames = f1 - f0 + 1


def roll12(gid, m, value):
    """Trailing 12-month sums on a dense gid x month panel.

    Returns (gids, windows) where windows[:, k] is the 12-month total ending
    in month f0 + k.
    """
    keep = (m >= w0) & (m <= f1)
    df = pd.DataFrame({"gid": gid[keep], "m": m[keep], "v": value[keep]})
    panel = (df.groupby(["gid", "m"])["v"].sum()
               .unstack(fill_value=0)
               .reindex(columns=range(w0, f1 + 1), fill_value=0))
    cs = np.cumsum(panel.to_numpy(dtype=float), axis=1)
    cs = np.hstack([np.zeros((cs.shape[0], 1)), cs])
    windows = cs[:, 12:] - cs[:, :-12]    # column k: months w0+k .. w0+k+11
    return panel.index.to_numpy(), windows


##### PEACEKEEPERS (RADPKO) #####
# personnel per cell-month, summed across missions; each frame shows the
# average monthly deployment over the trailing 12 months
radpko = pd.read_csv("./data/radpko/radpko_grid.csv",
                     usecols=["date", "prio.grid", "pko_deployed"])
pk_gid, pk_win = roll12(radpko["prio.grid"].to_numpy(dtype=int),
                        month_idx(radpko["date"]),
                        radpko["pko_deployed"].fillna(0).to_numpy())
pk_win = pk_win / 12
pk_max = pk_win.max()

##### VIOLENCE (ACLED) #####
# fatalities from all event types, 12-month total per cell
acled = pd.read_csv(ACLED_PATH, usecols=["event_date", "latitude", "longitude",
                                         "fatalities"])
vio_gid, vio_win = roll12(lonlat_gid(acled["longitude"].to_numpy(),
                                     acled["latitude"].to_numpy()),
                          month_idx(acled["event_date"]),
                          acled["fatalities"].to_numpy())
del acled

# continent-wide series for the timelines
vio_total = vio_win.sum(axis=0)
pk_total = pk_win.sum(axis=0)
months = np.arange(f0, f1 + 1)
years = months / 12                       # decimal years for the x axis


def vio_size(v, scale=1.0):
    """scatter `s` (points^2) for violence values, area-proportional, capped.

    `scale` multiplies circle diameters so each layout keeps the same circle
    size relative to its map.
    """
    return (scale * VIO_MAX_DIAM) ** 2 * np.minimum(v, VIO_CAP) / VIO_CAP


def pk_size(v, scale=1.0):
    return (scale * PK_MAX_DIAM) ** 2 * v / pk_max




##### FIGURE PIECES (built once per layout; each frame only updates data) #####
afr = (gpd.read_file("./data/gadm/africa/afr_g2014_2013_0.shp")
          .to_crs(4326)
          .simplify(0.02, preserve_topology=True))
vio_x, vio_y = gid_xy(vio_gid)
pk_x, pk_y = gid_xy(pk_gid)


def add_map(ax, xlim, ylim, scale):
    """Base map plus the two circle layers; returns an updater for frame k."""
    afr.plot(ax=ax, facecolor="#f7f7f7", edgecolor="#595959", linewidth=0.4)
    ax.set_xlim(xlim); ax.set_ylim(ylim)
    ax.set_aspect("equal")
    ax.set_axis_off()
    vio_pts = ax.scatter([], [], s=[], color=RED, alpha=0.45, linewidths=0, zorder=3)
    pk_pts = ax.scatter([], [], s=[], color=BLUE, alpha=0.5, linewidths=0, zorder=4)

    def update(k):
        v = vio_win[:, k]; on = v > 0
        vio_pts.set_offsets(np.column_stack([vio_x[on], vio_y[on]]))
        vio_pts.set_sizes(vio_size(v[on], scale))
        p = pk_win[:, k]; on = p > 0
        pk_pts.set_offsets(np.column_stack([pk_x[on], pk_y[on]]))
        pk_pts.set_sizes(pk_size(p[on], scale))
    return update


def add_legend(ax, col_x, row_y, label_dx, title_y, scale, fs=1.0):
    """Two legend columns that share row positions, in `ax` data coordinates.

    Circle sizes use the same mapping as the map layers.
    """
    vio_labels = [f"{b:,}" for b in VIO_BREAKS]
    vio_labels[-1] += "+"
    for x0, sizes, color, alpha, labels in [
            (col_x[0], vio_size(np.array(VIO_BREAKS), scale), RED, 0.45, vio_labels),
            (col_x[1], pk_size(np.array(PK_BREAKS), scale), BLUE, 0.5,
             [f"{b:,}" for b in PK_BREAKS])]:
        ax.scatter([x0] * 3, row_y, s=sizes, color=color, alpha=alpha,
                   linewidths=0, zorder=5, clip_on=False)
        for y, lab in zip(row_y, labels):
            ax.text(x0 + label_dx, y, lab, fontsize=8.5 * fs, color="#333333",
                    va="center", zorder=5)
    title_dx = 1.1 * label_dx
    ax.text(col_x[0] - title_dx, title_y,
            textwrap.fill(VIO_LABEL, 20) + "\n(12-month total)",
            fontsize=9 * fs, color=INK, va="top", linespacing=1.15)
    ax.text(col_x[1] - title_dx, title_y, "Peacekeepers\n(12-month avg.)",
            fontsize=9 * fs, color=INK, va="top", linespacing=1.15)


def add_timelines(ax_v, ax_p, fs=1.0):
    """Continent-wide series: full series in a light tint, the elapsed part in
    full color, and a cursor on the current month. Returns an updater."""
    thousands = FuncFormatter(lambda v, _: f"{v / 1000:,.0f}k" if v else "0")
    parts = []
    for a, series, color, label in [
            (ax_v, vio_total, RED, "Fatalities, all of Africa (12-month total)"),
            (ax_p, pk_total, BLUE, "Peacekeepers, all of Africa (12-month avg.)")]:
        a.fill_between(years, series, color=color, alpha=0.12, linewidth=0)
        a.plot(years, series, color=color, alpha=0.35, linewidth=1)
        fill = a.fill_between(years[:1], series[:1], color=color, alpha=0.35,
                              linewidth=0)
        line, = a.plot(years[:1], series[:1], color=color, linewidth=1.6)
        dot, = a.plot([], [], "o", color=color, markersize=4.5, zorder=4)
        cursor = a.axvline(years[0], color=INK, linewidth=0.8, zorder=3)
        parts.append({"ax": a, "series": series, "color": color, "fill": fill,
                      "line": line, "dot": dot, "cursor": cursor})
        a.set_ylim(0, series.max() * 1.5)     # headroom for the label
        a.yaxis.set_major_formatter(thousands)
        a.yaxis.set_major_locator(plt.MaxNLocator(2))
        a.text(0.005, 0.93, label, transform=a.transAxes, fontsize=8 * fs,
               color=MUTED, va="top")
        for side in ["top", "right"]:
            a.spines[side].set_visible(False)
        a.tick_params(labelsize=7.5 * fs, colors=MUTED, length=2)
    ax_v.tick_params(labelbottom=False)
    ax_p.set_xlim(years[0], years[-1])
    ax_p.set_xticks(range(2001, 2018, 2))

    def update(k):
        for part in parts:
            part["cursor"].set_xdata([years[k]] * 2)
            part["fill"].remove()
            part["fill"] = part["ax"].fill_between(
                years[:k + 1], part["series"][:k + 1], color=part["color"],
                alpha=0.35, linewidth=0)
            part["line"].set_data(years[:k + 1], part["series"][:k + 1])
            part["dot"].set_data([years[k]], [part["series"][k]])
    return update


def date_labels(fm):
    return idx_label(fm), f"12 months: {idx_label(fm - 11)} – {idx_label(fm)}"


##### LAYOUT #####
# returns (fig, draw) where draw(k) sets the figure to frame k

def build_tall():
    fig = plt.figure(figsize=(8.0, 9.6), dpi=100)
    ax = fig.add_axes([0.01, 0.255, 0.98, 0.65])
    ax_v = fig.add_axes([0.085, 0.175, 0.885, 0.065])
    ax_p = fig.add_axes([0.085, 0.1, 0.885, 0.065], sharex=ax_v)
    fig.text(0.015, 0.975, "UN peacekeepers and violence in Africa", fontsize=16,
             fontweight="bold", color=INK, va="top")
    fig.text(0.015, 0.943, VIO_LABEL, fontsize=11, color=MUTED, va="top")
    fig.text(0.015, 0.012, textwrap.fill(CAPTION, 150), fontsize=7.5,
             color=MUTED, va="bottom", linespacing=1.3)

    update_map = add_map(ax, (-26, 60), (-37, 38), scale=1.0)
    add_legend(ax, col_x=(-19.5, -2.5), row_y=[-9, -14, -21.5], label_dx=6,
               title_y=-2.5, scale=1.0)
    # date readout, over the Indian Ocean well below Madagascar
    date_txt = ax.text(58, -31, "", ha="right", va="center", fontsize=20,
                       fontweight="bold", color=INK)
    window_txt = ax.text(58, -34.5, "", ha="right", va="center", fontsize=8.5,
                         color="#666666")
    update_tl = add_timelines(ax_v, ax_p)

    def draw(k):
        update_map(k); update_tl(k)
        d, w = date_labels(f0 + k)
        date_txt.set_text(d); window_txt.set_text(w)
    return fig, draw


##### RENDER #####
def frame_rgb(fig):
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()


def render(build, dpi, name="tall", bg=PAGE_BG):
    """Stream every frame to an MP4."""
    with plt.rc_context({"figure.facecolor": bg, "axes.facecolor": bg}):
        fig, draw = build()
    fig.set_dpi(dpi)
    draw(0)
    h, w, _ = frame_rgb(fig).shape
    video = imageio_ffmpeg.write_frames(
        f"{WEB_DIR}/pk_violence_{name}.mp4", (w, h), fps=FPS, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        quality=None, output_params=["-crf", "24", "-preset", "slow",
                                     "-movflags", "+faststart"])
    video.send(None)
    # gif_frames = []  # GIF
    for k in range(n_frames):
        draw(k)
        rgb = frame_rgb(fig)
        video.send(rgb.tobytes())
        # gif_frames.append(Image.fromarray(rgb).resize(  # GIF
        #     (round(w * 100 / dpi), round(h * 100 / dpi)), Image.LANCZOS))
    for _ in range(HOLD_SECONDS * FPS):       # hold on the last frame
        video.send(rgb.tobytes())
    video.close()
    Image.fromarray(rgb).save(f"{WEB_DIR}/pk_violence_{name}.png", optimize=True)
    plt.close(fig)
    # write_gif(gif_frames, GIF_FILE, bg)  # GIF
    print(f"wrote pk_violence_{name} ({w}x{h})")


# GIF
# def write_gif(frames, path, bg):
#     # one shared palette (built from a sample of frames) so colors don't flicker
#     sample = frames[::max(1, len(frames) // 12)]
#     mosaic = Image.new("RGB", (frames[0].width, frames[0].height * len(sample)))
#     for j, im in enumerate(sample):
#         mosaic.paste(im, (0, j * frames[0].height))
#     palette = mosaic.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
#     idx = [np.asarray(im.quantize(palette=palette, dither=Image.Dither.NONE))
#            for im in frames]
#
#     # frames after the first only store changed pixels; the rest are marked
#     # transparent (index 255) so the previous frame shows through
#     CLEAR = 255
#     pal = palette.getpalette()[:255 * 3]
#     # median cut averages the background into a slightly different color;
#     # snap entries within a few levels of it back to the exact background
#     bg_rgb = np.array(matplotlib.colors.to_rgb(bg)) * 255
#     rgb = np.array(pal).reshape(-1, 3)
#     rgb[(np.abs(rgb - bg_rgb) <= 4).all(axis=1)] = bg_rgb.round().astype(int)
#     pal = rgb.ravel().tolist() + [255, 255, 255]
#     gif = []
#     for j, cur in enumerate(idx):
#         out = cur if j == 0 else np.where(cur == idx[j - 1], CLEAR, cur).astype(np.uint8)
#         im = Image.fromarray(out, mode="P")
#         im.putpalette(pal)
#         gif.append(im)
#
#     delay = round(1000 / FPS)
#     durations = [delay] * (len(gif) - 1) + [delay + HOLD_SECONDS * 1000]
#     gif[0].save(path, save_all=True, append_images=gif[1:], duration=durations,
#                 loop=0, optimize=False, disposal=1, transparency=CLEAR)


if __name__ == "__main__":
    render(build_tall, dpi=150)
    print(f"max violence {vio_win.max():,.0f}; share of cell-windows above cap "
          f"{(vio_win[vio_win > 0] > VIO_CAP).mean():.4f}")
