var underscore_name = "";
var number_name = "";
var dir = "";
var dest_directory = "";

//FUNCTION LIST
function runGaussianSubtraction(window) {
	selectWindow(window);
	run("Duplicate...", "title=1");
	selectWindow(window);
	run("Duplicate...", "title=2");
	selectWindow("2");
	run("Gaussian Blur...", "sigma=2");
	selectWindow("1");
	run("Gaussian Blur...", "sigma=1");
	imageCalculator("Subtract create", "1","2");
	selectWindow(window);
	close();
	selectWindow("1");
	close();
	selectWindow("2");
	close();
}

function renameWindow(old_name, new_name){
	selectWindow(old_name);
	rename(new_name);
}

function truncate(name, delimiter, offset){
	if (delimiter == ".") {
		return substring(name, 0, indexOf(name, "."));
	}
	if (delimiter == "_") {
		return substring(name, 0, lastIndexOf(name, "_") + 1);
	} else {
	return name;
	}
}

function generateMaximaMask(){
	setAutoThreshold("Default dark");
	setThreshold(20, 65535, "raw");
	call("ij.plugin.frame.ThresholdAdjuster.setMode", "B&W");
	setOption("BlackBackground", true);
	run("Convert to Mask");
}

function setProcessingSize(){
	Dialog.create("Choose an Option");
	Dialog.addChoice("Processing size:", newArray("8-bit", "16-bit"));
	Dialog.show();
	return Dialog.getChoice();
}

function setBatchSize(){
	Dialog.create("Choose Image Batch Size");
	Dialog.addNumber("Batch Size", 20);
	Dialog.show();
	return Dialog.getNumber();
}

function confirmStartup(){
	Dialog.create("Before Running...");
	Dialog.addMessage("It is highly recommended to process a single image separately before running the macro.\n" +
	"Ensure the measurements table includes RawIntDen.\n" +
	"DO NOT save the image in the same directory at the end of processing in order to keep the directory clean for MaskDirectory macro.\n" +
	"Proceed?");
	Dialog.show();
}


//MACROS
macro "CloseAll [F9]"{
	close("*");
	run("Close All");
}

// For masking single images one at a time
macro "MaskSingleImage [F1]"{
	confirmStartup();
	file_path = File.openDialog("Choose Image");
	dir = File.getDirectory(file_path);
	
	file_name = File.getName(file_path);
	
	underscore_name = truncate(file_name, "_", 1);
	number_name = truncate(file_name, ".", 0);
	dest_directory = dir + number_name + "/";
	File.makeDirectory(dir + number_name);
	
	processing_size = setProcessingSize();
	open(file_path);
	run(processing_size);
	
	source_file = dir + file_name;
	dest_file = dest_directory + file_name;			
	file_renamed = File.rename(source_file, dest_file);
	
	run("Stack to Images");
	
	renameWindow(underscore_name + "-0001", number_name + "-01");
	renameWindow(underscore_name + "-0002", number_name + "-02");
	
	runGaussianSubtraction(number_name + "-01");

	selectWindow("Result of 1");
	saveAs("Tiff", dest_directory + number_name + "_pre_threshold");
	
	generateMaximaMask();
	saveAs("Tiff", dest_directory + number_name + "_post_threshold");
	
	selectWindow(number_name + "-02");
	resetMinAndMax();
	setAutoThreshold("Default dark");
		
	run("Tile");
	run("Threshold...");
	
}

// for masking an entire directory at once, only images can be in this directory
macro "MaskDirectory [F2]" {
	confirmStartup();
    dir = getDirectory("Choose a Directory");
    list = getFileList(dir);
    processing_size = setProcessingSize();
    images_per_batch = setBatchSize();
    current_batch_count = 0;

    for (i = 0; i < list.length; i++) {
        file_path = dir + list[i];
        file_name = File.getName(file_path);

        underscore_name = truncate(file_name, "_", 1);
        number_name = truncate(file_name, ".", 0);
        dest_directory = dir + number_name + "/";
        File.makeDirectory(dir + number_name);
        
        open(file_path);
        run(processing_size);
        
        source_file = dir + file_name;
        dest_file = dest_directory + file_name;
        file_renamed = File.rename(source_file, dest_file);
        
        if (!file_renamed) {
            print("File not successfully renamed");
        }

        run("Stack to Images");
        renameWindow(underscore_name + "-0001", number_name + "-01");
        renameWindow(underscore_name + "-0002", number_name + "-02");
        
        runGaussianSubtraction(number_name + "-01");

        selectWindow("Result of 1");
        saveAs("Tiff", dest_directory + number_name + "_pre_threshold");
        
        generateMaximaMask();
        saveAs("Tiff", dest_directory + number_name + "_post_threshold");
        
        selectWindow(number_name + "-02");
        resetMinAndMax();
        setAutoThreshold("Default dark");
        
        current_batch_count++;

        // When 20 images have been opened, pause, close them, and start the next batch
        if (current_batch_count == images_per_batch) {
    		run("Tile");
    		run("Threshold...");
            waitForUser("Review image batch, then click OK to continue with the next batch.");
//            run("Close All");  // Close all open images after review
            current_batch_count = 0;  // Reset the batch counter for the next batch
        }
    }
    run("Tile");
    run("Threshold...");
}

// count foci, can only do individual images for now
macro "CountFoci [F3]" {
	current_window = getTitle();
	dash_index = lastIndexOf(current_window, "-");
	number_name = substring(current_window, 0, dash_index);
	dest_directory = dir + number_name + "/";
	
	run("Analyze Particles...", "size=200-Infinity show=Outlines exclude include overlay add");
	close();
	saveAs("Tiff", dest_directory + number_name + "_nucleiROI");
	close();
	 
	selectWindow(number_name + "_post_threshold.tif");
	run("From ROI Manager");
	run("Find Maxima...", "prominence=10 strict exclude output=[Single Points]");
	roiManager("Show All without labels");
	rename("Current Maxima" + number_name);
	roiManager("Measure");
	
	selectWindow(number_name + "_post_threshold.tif");
	close();
	selectWindow("Current Maxima" + number_name);
	close();
	//close("Results");
	
	nRows = nResults;
	for (i = 0; i < nRows; i++) {
	    raw_intensity = getResult("RawIntDen", i);
	    foci_count = raw_intensity / 255;
	    setResult("NumFoci", i, foci_count);
	}
	updateResults();
	saveAs("Results", dest_directory + number_name + "_results.csv");
	if (isOpen("Results")) {
		close("Results");
	}
	if (isOpen("ROI Manager")){
		close("ROI Manager");
	}
}