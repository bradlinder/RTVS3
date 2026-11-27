"""Build configuration constants and CLI argument parser."""
from __future__ import annotations

import argparse
import os

UV_VERSION = "0.12.12"
UV_URLS = {
    "win32-x86_64": f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-x86_64-pc-windows-msvc.zip",
    "win32-arm64": f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-aarch64-pc-windows-msvc.zip",
    "darwin-x86_64": f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-x86_64-apple-darwin.tar.gz",
    "darwin-arm64": f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-aarch64-apple-darwin.tar.gz",
    "linux-x86_64": f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz",
    "linux-aarch64": f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-aarch64-unknown-linux-gnu.tar.gz",
}

# Only the PySide6 submodules this app actually imports
PYSIDE6_USED_SUBMODULES = ["QtCore", "QtGui", "QtWidgets", "QtMultimedia", "QtMultimediaWidgets"]
PYSIDE6_EXCLUDES = [
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuick3D", "PySide6.QtQuickWidgets",
    "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.Qt3DInput", "PySide6.Qt3DExtras",
    "PySide6.Qt3DAnimation", "PySide6.Qt3DLogic",
    "PySide6.QtCharts", "PySide6.QtDataVisualization", "PySide6.QtGraphs", "PySide6.QtGraphsWidgets",
    "PySide6.QtBluetooth", "PySide6.QtNfc", "PySide6.QtPositioning", "PySide6.QtLocation",
    "PySide6.QtSensors", "PySide6.QtSerialPort", "PySide6.QtSerialBus",
    "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtDesigner", "PySide6.QtHelp",
    "PySide6.QtPdf", "PySide6.QtPdfWidgets", "PySide6.QtWebSockets", "PySide6.QtWebChannel",
    "PySide6.QtRemoteObjects", "PySide6.QtScxml", "PySide6.QtStateMachine",
    "PySide6.QtNetworkAuth", "PySide6.QtSpatialAudio",
]

# Heavy internal test and benchmarking trees to exclude from packaging
TEST_AND_BENCHMARK_EXCLUDES = [
    "scipy.cluster.tests", "scipy.interpolate.tests", "scipy.signal.tests",
    "scipy.sparse.tests", "scipy.special.tests", "scipy.ndimage.tests",
    "scipy.optimize.tests", "scipy.linalg.tests", "scipy.stats.tests",
    "scipy._lib.tests", "numpy.tests", "numpy.f2py.tests",
    "transformers.commands", "transformers.testing_utils",
    "sklearn.tests", "sklearn.datasets.tests", "sklearn.feature_extraction.tests",
    "pytest", "unittest.test",
    "triton", "nvidia", "tkinter", "tcl", "docutils", "IPython", "jupyter",
]

COLLECT_ALL_PACKAGES = [
    "faster_whisper", "ctranslate2", "huggingface_hub", "soundfile",
    "diarize", "silero_vad", "wespeakerruntime", "onnxruntime", "sherpa_onnx",
    "keyring", "docx", "pypdf", "numpy", "scipy", "sklearn", "torchaudio", "certifi",
    "spellchecker",
]

COPY_METADATA_PACKAGES = [
    "numpy", "scipy", "scikit-learn", "torch", "torchaudio",
    "silero_vad", "onnxruntime", "wespeakerruntime", "diarize",
    "sherpa-onnx", "ctranslate2", "faster_whisper", "soundfile",
    "pyspellchecker",
]

HIDDEN_IMPORTS = [
    "torch._C",
    "torch.testing",
    "torch.distributed",
    "torch.distributed.rpc",
    "numpy",
    "numpy.core",
    "numpy.core._multiarray_umath",
    "numpy.core.multiarray",
    "numpy._core",
    "numpy._core._multiarray_umath",
    "numpy._core.multiarray",
    "scipy",
    "scipy.signal",
    "scipy.spatial",
    "scipy.spatial.distance",
    "scipy.cluster",
    "scipy.cluster.hierarchy",
    "sklearn",
    "sklearn.cluster",
    "sklearn.utils",
    "sklearn.neighbors",
    "diarize",
    "diarize.clustering",
    "diarize.embeddings",
    "diarize.vad",
    "diarize.utils",
    "wespeakerruntime",
    "spellchecker",
    "spellcheck_helper",
    "spellcheck_widgets",
    "core_utils",
    "transcript_cleaner",
    "project_serialization",
    "process_lifecycle",
    "cache_manager",
    "remote_media_cache",
    "remote_media_cache_dialog",
    "story_widgets",
    "timeline_widgets",
    "transcript_editor",
    "comment_widgets",
    "background_workers",
    "thumbnail_workers",
    "batch_dialog",
    "theme_tokens",
    "bootstrap",
    "ui_layout",
    "transcript_story",
    "voice_profile_dialog",
    "model_cleanup_dialog",
    "speaker_dialogs",
    "story_detect_dialog",
    "story_fades_dialog",
    "shortcuts",
    "shortcuts.schema",
    "shortcuts.manager",
    "shortcuts.widgets",
    "shortcuts.dialogs",
    "shortcuts_manager",
    "processing",
    "runtime_manager",
    "radio_tv_story_segmenter_worker",
    "updater",
    "updater_core",
    "updater_workers",
    "updater_dialog",
    "export.daw",
    "export.subtitles",
    "export.pdf",
    "export.docx",
    "export.dialog",
    "export.story_selector",
    "export.reorder_dialog",
    "export.audio",
    "export.timeline",
    "backup_manager",
    "benchmark",
    "dialogs",
    "glossary_dialog",
    "id3_editor",
    "speaker_name_cleanup_dialog",
    "speaker_profiles_dialog",
    "user_guide_dialog",
    "plugins.manager",
]


def parse_build_args():
    """Parse build target, plugin selection, installer, and version CLI flags."""
    parser = argparse.ArgumentParser(description="Build Radio & TV Segmenter and plugins.")
    parser.add_argument(
        "--target",
        default=os.environ.get("BUILD_TARGET", "all"),
        help="Build target: 'all' / 'Core App + Selected Plugins', 'core' / 'Core App Only', or 'plugins' / 'Plugins Only'.",
    )
    parser.add_argument(
        "--plugin",
        dest="single_plugin",
        default=os.environ.get("BUILD_SINGLE_PLUGIN", None),
        help="Build a specific individual plugin only: 'wordpress', 'youtube', 'translation', or 'all'.",
    )
    parser.add_argument(
        "--plugin-wordpress",
        type=lambda x: str(x).lower() in ("true", "1", "yes"),
        default=os.environ.get("BUILD_PLUGIN_WORDPRESS", "true").lower() in ("true", "1", "yes"),
        help="Include WordPress Publisher plugin.",
    )
    parser.add_argument(
        "--plugin-youtube",
        type=lambda x: str(x).lower() in ("true", "1", "yes"),
        default=os.environ.get("BUILD_PLUGIN_YOUTUBE", "true").lower() in ("true", "1", "yes"),
        help="Include YouTube Video Publisher plugin.",
    )
    parser.add_argument(
        "--plugin-translation",
        type=lambda x: str(x).lower() in ("true", "1", "yes"),
        default=os.environ.get("BUILD_PLUGIN_TRANSLATION", "true").lower() in ("true", "1", "yes"),
        help="Include Language Translation plugin.",
    )
    parser.add_argument(
        "--installer",
        action="store_true",
        help="Force compilation of Windows setup installer executable.",
    )
    parser.add_argument(
        "--no-installer",
        action="store_true",
        help="Skip automatic compilation of Windows installer (useful when CI compiles in a separate step).",
    )
    parser.add_argument(
        "--bundle-uv",
        action="store_true",
        default=os.environ.get("BUILD_BUNDLE_UV", "false").lower() in ("true", "1", "yes"),
        help="Pre-bundle standalone uv binary in optional_runtime/ (default False to save ~50MB; runtime_manager fetches on-demand if optional runtimes are requested).",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="Explicit project version to use for output packages and installer filenames.",
    )
    args = parser.parse_known_args()[0]
    if args.single_plugin:
        p = str(args.single_plugin).strip().lower()
        if p == "wordpress":
            args.plugin_wordpress = True
            args.plugin_youtube = False
            args.plugin_translation = False
        elif p == "youtube":
            args.plugin_wordpress = False
            args.plugin_youtube = True
            args.plugin_translation = False
        elif p == "translation":
            args.plugin_wordpress = False
            args.plugin_youtube = False
            args.plugin_translation = True
        elif p in ("all", "plugins"):
            args.plugin_wordpress = True
            args.plugin_youtube = True
            args.plugin_translation = True
        if str(args.target).strip().lower() == "all" and p not in ("all",):
            args.target = "plugins"
    return args
