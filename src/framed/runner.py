import subprocess
import os
import shutil
import tempfile
import atexit
from pathlib import Path
from .config import Config
from .simctl import Simctl

class Runner:
    def __init__(self, config: Config):
        self.config = config

    def run(self):
        """Execute the screenshot capture pipeline for all configured devices and languages."""
        from .extractor import Extractor
        
        scheme = self.config.scheme
        project = self.config.project
        raw_output_dir = Path(self.config.output_dir) / "raw"
        if raw_output_dir.exists():
            shutil.rmtree(raw_output_dir)
        raw_output_dir.mkdir(parents=True)
        
        extractor = Extractor()

        for device in self.config.devices:
            print(f"📱 Preparing device: {device['name']}")
            for lang in self.config.languages:
                print(f"  🌏 Capturing in {lang}...")
                
                # Cleanup is AUTOMATIC with TemporaryDirectory
                with tempfile.TemporaryDirectory(prefix="framed_xcresult_") as temp_dir:
                    result_bundle_path = Path(temp_dir) / f"Test.xcresult"
                    
                    try:
                        Simctl.set_status_bar("booted")
                    except Exception:
                        pass # Ignore if no booted device found, xcodebuild will launch it later (retry logic would be better but keeping simple)

                    cmd = [
                        "xcodebuild", "test",
                        "-scheme", scheme,
                        "-project", project,
                        "-destination", f"platform=iOS Simulator,name={device['name']}",
                        "-testLanguage", lang,
                        "-testRegion", lang,
                        "-resultBundlePath", str(result_bundle_path)
                    ]
                    
                    try:
                        subprocess.run(cmd, check=True, capture_output=True) 
                    except subprocess.CalledProcessError as e:
                        print(f"    ❌ Test failed for {lang}:")
                        print(e.stderr.decode('utf-8') if e.stderr else "Unknown error")
                        continue

                    print(f"    📦 Extracting screenshots...")
                    
                    # Create specific output dir for this run to avoid overwrites
                    # e.g. docs/screenshots/raw/iPhone 17_ja/
                    run_output_dir = raw_output_dir / f"{device['name']}_{lang}"
                    run_output_dir.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        extractor.process_xcresult(result_bundle_path, run_output_dir)
                    except Exception as e:
                        print(f"❌ Extractor error: {e}")

        # 3. Process (Frame & Text)
        print("\n🎨 Processing screenshots...")
        try:
            from .processor import Processor
            processor = Processor(self.config)
            processor.process()
        except Exception as e:
            print(f"❌ Processing failed: {e}")
