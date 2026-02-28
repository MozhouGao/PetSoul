"""
Main Pipeline
Orchestrates the complete pet 3D model generation workflow
"""

import logging
import numpy as np
from typing import Dict, Optional
from pet_detector import PetDetector
from attribute_extractor import AttributeExtractor
from prompt_builder import PromptBuilder
from meshy_generator import MeshyGenerator
from pet_profile import PetProfile

from config import CONFIG

logger = logging.getLogger(__name__)


class Pet3DModelPipeline:
    """
    Complete pipeline: Image -> Pet Profile -> 3D Model
    Generates 3D models of pets from photos
    """

    def __init__(
        self,
        use_clip: bool = True,
        use_sam: bool = False,  # Optional segmentation (not implemented in MVP)
        output_format: str = "glb"
    ):
        """
        Initialize pipeline

        Args:
            use_clip: Use CLIP for attribute extraction
            use_sam: Use SAM for segmentation (optional, not in MVP)
            output_format: 3D model output format ('glb', 'obj', 'ply', 'stl')
        """
        logger.info("Initializing Pet 3D Model Pipeline...")

        # Step 1: Pet Detection
        self.detector = PetDetector()

        # Step 2: Attribute Extraction
        self.extractor = AttributeExtractor(use_clip=use_clip)

        # Step 3: Prompt Building (still useful for metadata)
        self.prompt_builder = PromptBuilder()

        # Step 4: 3D Model Generation (Meshy.ai API)
        self.generator = MeshyGenerator(
            ai_model=CONFIG.meshy_ai_model,
            target_polycount=CONFIG.meshy_target_polycount,
            topology=CONFIG.meshy_topology,
            enable_pbr=CONFIG.meshy_enable_pbr,
            poll_interval=CONFIG.meshy_poll_interval,
            timeout=CONFIG.meshy_timeout,
        )

        self.output_format = output_format

        logger.info("Pipeline initialized")

    def process(
        self,
        image: np.ndarray,
        output_path: Optional[str] = None,
    ) -> Dict:
        """
        Complete processing pipeline

        Args:
            image: Input image as numpy array (RGB format)
            output_path: Path to save 3D model file (optional)

        Returns:
            Dictionary with:
                - profile: PetProfile dict
                - mesh_data: Generated 3D mesh data or None
                - model_path: Path to saved 3D model file (if output_path provided)
                - prompt: Generation metadata prompt
                - error: Error message if failed
        """
        try:
            if len(image.shape) != 3 or image.shape[2] != 3:
                return {"error": "Invalid image format"}

            # Input is already RGB — use directly
            rgb_image = image

            # Step 1: Pet Detection
            logger.info("Step 1: Detecting pet...")
            bbox = self.detector.detect(rgb_image)
            if bbox is None:
                return {"error": "No pet detected in image"}

            pet_crop = self.detector.crop_pet(rgb_image, bbox)
            if pet_crop is None:
                return {"error": "Failed to crop pet from image"}

            logger.info("Pet detected and cropped: %s", pet_crop.shape)

            # Step 2: Attribute Extraction
            logger.info("Step 2: Extracting attributes...")
            breed, breed_conf = self.extractor.extract_breed(pet_crop)
            coat_colors = self.extractor.extract_coat_colors(pet_crop)
            markings = self.extractor.extract_markings(pet_crop)

            # Extract physical attributes for procedural generation
            logger.info("Step 2b: Extracting physical attributes...")
            physical = self.extractor.extract_physical_attributes(pet_crop)

            # Create pet profile
            profile = PetProfile(
                species="dog",  # MVP: dog-only
                breed=breed,
                breed_confidence=breed_conf,
                coat_colors=coat_colors,
                markings=markings,
                fur_length=physical.get("fur_length"),
                body_type=physical.get("body_type"),
                ear_shape=physical.get("ear_shape"),
                tail_type=physical.get("tail_type"),
                snout_length=physical.get("snout_length"),
                size_class=physical.get("size_class"),
            )

            logger.info("Attributes extracted: %s, colors: %s, markings: %s, physical: %s",
                         breed, coat_colors, markings, physical)

            # Step 3: Prompt Construction (for texture detail)
            logger.info("Step 3: Building texture prompt...")
            prompt = self.prompt_builder.build_prompt(profile, style="realistic")

            logger.debug("Texture prompt: %s", prompt[:200])

            # Step 4: 3D Model Generation via Meshy.ai
            # Pass pet_crop as both the shape source and texture reference
            logger.info("Step 4: Generating 3D model via Meshy API...")
            mesh_data = self.generator.generate(
                image=pet_crop,
                output_format=self.output_format,
                texture_prompt=prompt,
                texture_image=pet_crop,
            )

            if mesh_data is None or not mesh_data.get("success"):
                return {
                    "error": "Failed to generate 3D model",
                    "profile": profile.to_dict(),
                    "prompt": prompt
                }

            logger.info("3D model generated successfully")
            logger.debug("Pet crop shape: %s", pet_crop.shape)

            result = {
                "profile": profile.to_dict(),
                "mesh_data": mesh_data,
                "prompt": prompt,
            }

            # Save to file if output path provided
            if output_path:
                logger.info("Step 5: Saving 3D model to %s...", output_path)
                if self.generator.save_mesh(mesh_data, output_path, self.output_format):
                    result["model_path"] = output_path
                    logger.info("3D model saved to %s", output_path)
                else:
                    result["error"] = "Failed to save 3D model"

            return result

        except Exception as e:
            logger.exception("Pipeline error")
            return {"error": str(e)}

    def is_ready(self) -> bool:
        """Check if pipeline is ready"""
        return (
            self.detector.is_ready() and
            self.generator.is_ready()
        )


# Backward compatibility alias
PetAvatarPipeline = Pet3DModelPipeline
