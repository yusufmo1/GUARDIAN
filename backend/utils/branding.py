"""
Branding and Corporate Identity Utilities

Utilities for managing corporate branding, logos, color schemes, and
styling across the GUARDIAN system. Provides consistent access to
branding resources and configuration.

Features:
- Centralized branding configuration management
- Logo and asset resolution
- Color scheme utilities
- Template customization support
- Print and digital styling optimization
"""
import json
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass

from ..config.settings import settings
from . import logger

@dataclass
class ColorScheme:
    """
    Color scheme configuration.
    
    Attributes:
        primary: Primary brand color
        secondary: Secondary brand color
        accent: Accent color for highlights
        success: Success state color
        warning: Warning state color
        danger: Danger/error state color
        light_bg: Light background color
        dark_bg: Dark background color
        text_primary: Primary text color
        text_secondary: Secondary text color
        text_muted: Muted text color
    """
    primary: str
    secondary: str
    accent: str
    success: str
    warning: str
    danger: str
    light_bg: str
    dark_bg: str
    text_primary: str
    text_secondary: str
    text_muted: str

@dataclass
class LogoInfo:
    """
    Logo information and configuration.
    
    Attributes:
        file: Logo filename
        alt_text: Alternative text for accessibility
        width: Preferred width in pixels
        height: Preferred height in pixels
        format: File format (PNG, SVG, etc.)
        path: Full path to logo file
    """
    file: str
    alt_text: str
    width: int
    height: int
    format: str
    path: Optional[str] = None

@dataclass
class TypographyConfig:
    """
    Typography configuration.
    
    Attributes:
        primary_font: Primary font family
        secondary_font: Secondary font family
        monospace_font: Monospace font family
        font_sizes: Dictionary of font sizes
        line_heights: Dictionary of line heights
    """
    primary_font: str
    secondary_font: str
    monospace_font: str
    font_sizes: Dict[str, str]
    line_heights: Dict[str, str]

@dataclass
class BrandingConfig:
    """
    Complete branding configuration.
    
    Attributes:
        organization: Organization information
        colors: Color scheme
        logos: Logo configurations
        typography: Typography settings
        layout: Layout configuration
        themes: Available themes
        metadata: Configuration metadata
    """
    organization: Dict[str, str]
    colors: ColorScheme
    logos: Dict[str, LogoInfo]
    typography: TypographyConfig
    layout: Dict[str, str]
    themes: Dict[str, Dict[str, str]]
    metadata: Dict[str, str]

class BrandingManager:
    """
    Manager for corporate branding and styling.
    
    Provides centralized access to branding configuration,
    logo resolution, and styling utilities.
    """
    
    def __init__(self):
        """Initialize branding manager."""
        self.static_dir = Path(__file__).parent.parent / "static"
        self.logos_dir = self.static_dir / "images" / "logos"
        self.branding_file = self.static_dir / "branding.json"
        
        # Create directories if they don't exist
        self.logos_dir.mkdir(parents=True, exist_ok=True)
        
        # Load branding configuration
        self._config = self._load_branding_config()
        
        logger.info("Branding manager initialized", 
                   static_dir=str(self.static_dir),
                   logos_dir=str(self.logos_dir))
    
    def _load_branding_config(self) -> BrandingConfig:
        """
        Load branding configuration from JSON file.
        
        Returns:
            BrandingConfig object
        """
        try:
            if self.branding_file.exists():
                with open(self.branding_file, 'r') as f:
                    config_data = json.load(f)
                
                # Parse color scheme
                colors = ColorScheme(**config_data.get('branding', {}))
                
                # Parse logos
                logos = {}
                for logo_name, logo_data in config_data.get('logos', {}).items():
                    logo_info = LogoInfo(**logo_data)
                    # Resolve full path
                    logo_info.path = str(self.logos_dir / logo_info.file)
                    logos[logo_name] = logo_info
                
                # Parse typography
                typography = TypographyConfig(**config_data.get('typography', {}))
                
                return BrandingConfig(
                    organization=config_data.get('organization', {}),
                    colors=colors,
                    logos=logos,
                    typography=typography,
                    layout=config_data.get('layout', {}),
                    themes=config_data.get('themes', {}),
                    metadata=config_data.get('metadata', {})
                )
            else:
                logger.warning("Branding configuration file not found, using defaults")
                return self._get_default_config()
                
        except Exception as e:
            logger.error(f"Failed to load branding configuration: {str(e)}")
            return self._get_default_config()
    
    def _get_default_config(self) -> BrandingConfig:
        """
        Get default branding configuration.
        
        Returns:
            Default BrandingConfig
        """
        colors = ColorScheme(
            primary="#003f5c",
            secondary="#d62728",
            accent="#ff7f0e",
            success="#28a745",
            warning="#ffc107",
            danger="#dc3545",
            light_bg="#f8f9fa",
            dark_bg="#2c3e50",
            text_primary="#2c3e50",
            text_secondary="#6c757d",
            text_muted="#868e96"
        )
        
        logos = {
            "primary": LogoInfo(
                file="qmul_logo.svg",
                alt_text="Queen Mary University of London",
                width=200,
                height=60,
                format="SVG",
                path=str(self.logos_dir / "qmul_logo.svg")
            ),
            "secondary": LogoInfo(
                file="ucb_logo.svg",
                alt_text="UCB Pharma",
                width=180,
                height=50,
                format="SVG",
                path=str(self.logos_dir / "ucb_logo.svg")
            )
        }
        
        typography = TypographyConfig(
            primary_font="Arial, 'Helvetica Neue', Helvetica, sans-serif",
            secondary_font="'Times New Roman', Times, serif",
            monospace_font="'Courier New', Courier, monospace",
            font_sizes={
                "xs": "0.75rem",
                "sm": "0.875rem",
                "base": "1rem",
                "lg": "1.125rem",
                "xl": "1.25rem",
                "2xl": "1.5rem",
                "3xl": "1.875rem",
                "4xl": "2.25rem",
                "5xl": "3rem"
            },
            line_heights={
                "tight": "1.25",
                "normal": "1.5",
                "relaxed": "1.75"
            }
        )
        
        return BrandingConfig(
            organization={
                "name": "Queen Mary University of London",
                "department": "School of Biological and Chemical Sciences",
                "website": "https://www.qmul.ac.uk"
            },
            colors=colors,
            logos=logos,
            typography=typography,
            layout={
                "max_width": "1200px",
                "container_padding": "20px",
                "border_radius": "8px"
            },
            themes={
                "light": {
                    "background": "#ffffff",
                    "surface": "#f8f9fa",
                    "text": "#2c3e50"
                },
                "dark": {
                    "background": "#1a202c",
                    "surface": "#2d3748",
                    "text": "#e2e8f0"
                }
            },
            metadata={
                "version": "1.0.0",
                "source": "default_config"
            }
        )
    
    def get_branding_config(self) -> BrandingConfig:
        """
        Get complete branding configuration.
        
        Returns:
            BrandingConfig object
        """
        return self._config
    
    def get_color_scheme(self, theme: str = "light") -> ColorScheme:
        """
        Get color scheme for specified theme.
        
        Args:
            theme: Theme name (light, dark, academic)
            
        Returns:
            ColorScheme object
        """
        return self._config.colors
    
    def get_logo_info(self, logo_name: str = "primary") -> Optional[LogoInfo]:
        """
        Get logo information by name.
        
        Args:
            logo_name: Name of logo (primary, secondary, favicon)
            
        Returns:
            LogoInfo if found, None otherwise
        """
        return self._config.logos.get(logo_name)
    
    def get_logo_path(self, logo_name: str = "primary") -> Optional[str]:
        """
        Get full path to logo file.
        
        Args:
            logo_name: Name of logo
            
        Returns:
            Full path to logo file if found, None otherwise
        """
        logo_info = self.get_logo_info(logo_name)
        if logo_info and logo_info.path and Path(logo_info.path).exists():
            return logo_info.path
        return None
    
    def get_organization_info(self) -> Dict[str, str]:
        """
        Get organization information.
        
        Returns:
            Organization information dictionary
        """
        return self._config.organization
    
    def get_typography_config(self) -> TypographyConfig:
        """
        Get typography configuration.
        
        Returns:
            TypographyConfig object
        """
        return self._config.typography
    
    def get_css_variables(self, theme: str = "light") -> Dict[str, str]:
        """
        Get CSS custom properties for the specified theme.
        
        Args:
            theme: Theme name
            
        Returns:
            Dictionary of CSS variable name/value pairs
        """
        colors = self._config.colors
        typography = self._config.typography
        layout = self._config.layout
        
        # Get theme-specific colors
        theme_colors = self._config.themes.get(theme, {})
        
        css_vars = {
            # Colors
            "--primary-color": colors.primary,
            "--secondary-color": colors.secondary,
            "--accent-color": colors.accent,
            "--success-color": colors.success,
            "--warning-color": colors.warning,
            "--danger-color": colors.danger,
            "--light-bg": colors.light_bg,
            "--dark-bg": colors.dark_bg,
            "--text-primary": colors.text_primary,
            "--text-secondary": colors.text_secondary,
            "--text-muted": colors.text_muted,
            
            # Theme-specific overrides
            "--theme-background": theme_colors.get("background", colors.light_bg),
            "--theme-surface": theme_colors.get("surface", "#ffffff"),
            "--theme-text": theme_colors.get("text", colors.text_primary),
            "--theme-border": theme_colors.get("border", "#dee2e6"),
            
            # Typography
            "--font-family": typography.primary_font,
            "--font-family-secondary": typography.secondary_font,
            "--font-family-mono": typography.monospace_font,
            
            # Layout
            "--max-width": layout.get("max_width", "1200px"),
            "--container-padding": layout.get("container_padding", "20px"),
            "--border-radius": layout.get("border_radius", "8px"),
            "--box-shadow": layout.get("box_shadow", "0 4px 6px rgba(0,0,0,0.1)"),
            "--transition": layout.get("transition", "all 0.3s ease")
        }
        
        # Add font sizes
        for size_name, size_value in typography.font_sizes.items():
            css_vars[f"--font-size-{size_name}"] = size_value
        
        # Add line heights
        for height_name, height_value in typography.line_heights.items():
            css_vars[f"--line-height-{height_name}"] = height_value
        
        return css_vars
    
    def generate_theme_css(self, theme: str = "light") -> str:
        """
        Generate CSS with theme variables.
        
        Args:
            theme: Theme name
            
        Returns:
            CSS string with custom properties
        """
        css_vars = self.get_css_variables(theme)
        
        css_lines = [":root {"]
        for var_name, var_value in css_vars.items():
            css_lines.append(f"  {var_name}: {var_value};")
        css_lines.append("}")
        
        return "\n".join(css_lines)
    
    def get_report_branding_options(self, custom_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get branding options formatted for report generation.
        
        Args:
            custom_options: Custom branding overrides
            
        Returns:
            Branding options dictionary for reports
        """
        colors = self._config.colors
        organization = self._config.organization
        typography = self._config.typography
        
        # Get logo paths
        primary_logo = self.get_logo_path("primary")
        secondary_logo = self.get_logo_path("secondary")
        
        branding_options = {
            # Organization
            "organization_name": organization.get("name", "Queen Mary University of London"),
            "department": organization.get("department", "School of Biological and Chemical Sciences"),
            
            # Colors
            "primary_color": colors.primary,
            "secondary_color": colors.secondary,
            "accent_color": colors.accent,
            
            # Typography
            "font_family": typography.primary_font,
            
            # Logos
            "primary_logo": primary_logo,
            "secondary_logo": secondary_logo
        }
        
        # Apply custom overrides
        if custom_options:
            branding_options.update(custom_options)
        
        return branding_options
    
    def list_available_logos(self) -> List[Dict[str, Any]]:
        """
        List all available logos with their information.
        
        Returns:
            List of logo information dictionaries
        """
        logos = []
        
        for logo_name, logo_info in self._config.logos.items():
            logo_dict = {
                "name": logo_name,
                "file": logo_info.file,
                "alt_text": logo_info.alt_text,
                "width": logo_info.width,
                "height": logo_info.height,
                "format": logo_info.format,
                "path": logo_info.path,
                "exists": Path(logo_info.path).exists() if logo_info.path else False
            }
            logos.append(logo_dict)
        
        return logos
    
    def list_available_themes(self) -> List[str]:
        """
        List all available themes.
        
        Returns:
            List of theme names
        """
        return list(self._config.themes.keys())
    
    def validate_branding_assets(self) -> Dict[str, Any]:
        """
        Validate that all branding assets exist and are accessible.
        
        Returns:
            Validation report with status and issues
        """
        issues = []
        missing_logos = []
        
        # Check logo files
        for logo_name, logo_info in self._config.logos.items():
            if not logo_info.path or not Path(logo_info.path).exists():
                missing_logos.append(logo_name)
                issues.append(f"Logo '{logo_name}' not found at {logo_info.path}")
        
        # Check branding configuration file
        if not self.branding_file.exists():
            issues.append(f"Branding configuration file not found: {self.branding_file}")
        
        status = "valid" if not issues else "issues_found"
        
        return {
            "status": status,
            "issues": issues,
            "missing_logos": missing_logos,
            "available_logos": len(self._config.logos),
            "available_themes": len(self._config.themes),
            "config_source": self._config.metadata.get("source", "unknown")
        }

# Create global instance
branding_manager = BrandingManager()