library(raster)
library(stringr)

### VARIABLES
# Path Env data
env.dir <- "R:/IMAS/Antarctic_Seafloor/environmental_data/"
# Path Bio data
bio.dir <- "R:/IMAS/Antarctic_Seafloor/Clean_Data_For_Permanent_Storage"
# Survey
survey <- "PS96"
# Metadata suffix
metadata.suffix <- "_1_raw_images_and_metadata/metadata"
# CoralNet suffix
coralnet.suffix <- "_4_annotation_library_cover"
# Metadata fname
metadata.fname <- "PS96_dat_FINAL.Rdata"
metadata.path <- paste0(c(bio.dir, survey, paste0(survey, metadata.suffix), 
                          metadata.fname), collapse="/")
# CSV fname
coralnet.csv.fname <- "PS96_annotations_03_201912.csv"
coralnet.csv.path <- paste0(c(bio.dir, survey, paste0(survey, coralnet.suffix), 
                            coralnet.csv.fname), collapse="/")
# CSV labels of interest
labels.fname <- "C:/Users/cgros/code/biigle_scripts/coralnet_to_biigle.csv"
labels.name <- cbind(read.csv(labels.fname)[,1])
labels.unscorable <- c("NoID", "NoID_ExpOp", "NoID_TBD", "Unscorable")
# Output file
output.fname <- "R:/IMAS/Antarctic_Seafloor/Clean_Data_For_Permanent_Storage/PS96/PS96_6_VMEs_annotation_library_counts/coralNet_count_envGrid.csv"

### BATHYMETRY
depth <- raster(paste0(env.dir,"Circumpolar_EnvData_bathy_fulldepth.gri"))$depth
stereo <- as.character(depth@crs)

# BIOLOGICAL DATA
dat.coralnet.full <- read.csv(coralnet.csv.path, header=TRUE)
dat.metadata.full <- get(load(metadata.path))
# Get metadata data of interest, ie discard images not included in labelling
coralnet.fname <- dat.coralnet.full$Name
image.fname <- str_split_fixed(str_split_fixed(dat.coralnet.full$Name, "__", 2)[,-1], 
                      ".jpg", 2)[, 1]
image.fname <- cbind(image.fname)
dat.metadata <- subset(dat.metadata.full, Filename %in% image.fname)
# Match column names betweem the two dataframes
dat.coralnet.full$Filename <- image.fname
dat.coralnet.clean <- dat.coralnet.full[c("Filename", "Label")]
# Get coralNet data of interest, ie discard images not included in labelling
dat.coralnet <- subset(dat.coralnet.clean, Label %in% c(labels.name, labels.unscorable))
# Create biological dataframe
col.names <- c(c("Filename", "Longitude", "Latitude"), 
               c(labels.name, labels.unscorable))
dat.bio <- data.frame(matrix(ncol = length(col.names), nrow = 0))
colnames(dat.bio) <- col.names
for (row in 1:nrow(dat.metadata)) {
  metadata.current <- dat.metadata[row, c("Filename", "Longitude", "Latitude")]
  filename.current <-  dat.metadata[row, "Filename"]
  coralnet.current <- dat.coralnet[dat.coralnet$Filename == filename.current, ]
  occurences <- data.frame(rbind(table(coralnet.current$Label)))
  labels.missing <- setdiff(c(labels.name, labels.unscorable), colnames(occurences))
  occurences[labels.missing] <- 0
  dat.bio <- rbind(dat.bio, cbind(metadata.current, occurences))
}

# PROJECTION on environmental grid
spatial.dat <- data.frame(cbind(dat.bio$Longitude, dat.bio$Latitude))
names(spatial.dat) <- c("Longitude","Latitude")
coordinates(spatial.dat) <- c("Longitude","Latitude")
proj4string(spatial.dat) <- CRS("+proj=longlat +datum=WGS84")
polar.dat.bio <- spTransform(spatial.dat, CRS(stereo))
cell.id <- extract(depth, polar.dat.bio, cellnumbers=TRUE)[,1]
cell=cell.id
dat.bio <- cbind(cell, dat.bio)

# SAVE RESULT
write.csv(dat.bio, output.fname, row.names = FALSE)