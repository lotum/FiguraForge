# Third-party notices

FiguraForge application code is newly authored for this project and provided
under the MIT license. It does not vendor PartPin, SnapSplit, PrintSplit,
DitherForge, Hunyuan3D or TRELLIS source code or model weights.

Python packages are installed separately through pyproject.toml. Their licenses,
not this project's MIT license, govern those dependencies. The generated
`docs/dependency-versions.json` records the package metadata visible in the
test environment. This is not a transitive-license compliance certificate.

Important dependencies include FastAPI, Uvicorn, Pydantic, NumPy, SciPy,
Trimesh, Shapely, Pillow, VTK, scikit-image, httpx and cryptography. Consult
their installed dist-info metadata and distributions for full license texts.

SpoolmanDB data is not embedded in the default catalog. The application can
retrieve/import it at the user's request; its repository's data terms remain
applicable. Default DEMO colors are synthetic and are not manufacturer claims.

The original procedural teddy GLB is dedicated under CC0 1.0; see
examples/LICENSE.md. User images, third-party character designs, generated
provider assets and printed objects have their own applicable permissions and
provider terms. The source-code license does not grant rights to a character.
