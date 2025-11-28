"""Asset loading utilities for textures and game resources."""

from PIL import Image
from OpenGL.GL import *

# Cache for loaded textures to avoid reloading
_texture_cache = {}


def load_texture(path):
    """Load an image from disk into an OpenGL texture.
    
    Args:
        path: Path to the image file.
        
    Returns:
        OpenGL texture ID.
    """
    if path in _texture_cache:
        return _texture_cache[path]

    img = Image.open(path)
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    img = img.convert('RGBA')
    img_data = img.tobytes()

    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    try:
        glGenerateMipmap(GL_TEXTURE_2D)
    except Exception:
        pass

    _texture_cache[path] = tex
    return tex

def cleanup_textures():
    """Clean up all cached textures."""
    for tex in _texture_cache.values():
        try:
            glDeleteTextures([tex])
        except Exception:
            pass
    _texture_cache.clear()
