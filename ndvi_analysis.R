library(raster)
library(sf)

analyse_ndvi <- function(image_path, shapefile_path = NULL) {
  img <- stack(image_path)
  nir <- img[[4]]
  red <- img[[3]]
  
  ndvi <- (nir - red) / (nir + red)
  
  if (!is.null(shapefile_path)) {
    zone <- st_read(shapefile_path)
    ndvi_masque <- mask(ndvi, zone)
    ndvi_mean <- cellStats(ndvi_masque, mean, na.rm = TRUE)
    cat("NDVI moyen:", ndvi_mean, "\n")
  }
  
  return(ndvi)
}

args <- commandArgs(trailingOnly = TRUE)
if (length(args) > 0) {
  analyse_ndvi(args[1], args[2])
}
