var underscore_name = "";
var number_name = "";
var dir = "";
var dest_directory = "";
var previous_nRows = 0;

//FUNCTION LIST
// run gaussian subtraction on duplicated images
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

// rename image window
function renameWindow(old_name, new_name){
	selectWindow(old_name);
	rename(new_name);
}

// truncate file_name using specified delimiter
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

// generate binary mask using threshold (necessary?)
function generateMaximaMask(i){
	// I think this might be what is acting up when running on entire directory
	setAutoThreshold("Default dark");
	setThreshold(i, 65535, "raw");
//	call("ij.plugin.frame.ThresholdAdjuster.setMode", "B&W");
	setOption("BlackBackground", true);
	run("Convert to Mask");
}

// set processing size for image (8- or 16-bit)
function setProcessingSize(){
	Dialog.create("Choose an Option");
	Dialog.addChoice("Processing size:", newArray("8-bit", "16-bit"));
	Dialog.show();
	return Dialog.getChoice();
}

// set how many images to process at a time when using MaskDirectory macro
function setBatchSize(){
	Dialog.create("Choose Image Batch Size");
	Dialog.addNumber("Batch Size", 20);
	Dialog.show();
	return Dialog.getNumber();
}

function setMaskThreshold(){
	Dialog.create("Choose threshold for focus processing");
	Dialog.addNumber("Threshold", 50);
	Dialog.show();
	return Dialog.getNumber();
}

// confirmation to ensure that the final results table includes the necessary measurements
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
	
	processing_size = setProcessingSize();
	thresh = setMaskThreshold();
	
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
	
	run("Stack to Images");
	
	// rename windows so that they don't have a lot of zeroes, not really necessary but makes troubleshooting easier
	renameWindow(underscore_name + "-0001", number_name + "-Halo");
	renameWindow(underscore_name + "-0002", number_name + "-DAPI");
	
	runGaussianSubtraction(number_name + "-Halo");

	// before thresholding, save result of gaussian subtraction
	selectWindow("Result of 1");
	saveAs("Tiff", dest_directory + number_name + "_pre_threshold");
	
	generateMaximaMask(thresh);
	
	saveAs("Tiff", dest_directory + number_name + "_post_threshold");
	
	selectWindow(number_name + "-DAPI");
	resetMinAndMax();
	setAutoThreshold("Default dark");
		
	run("Tile");
	run("Threshold...");
	
}

// for masking an entire directory at once, only images can be in the selected directory for it to work
macro "MaskDirectory [F2]" {
	confirmStartup();
    dir = getDirectory("Choose a Directory");
    list = getFileList(dir);
    processing_size = setProcessingSize();
    images_per_batch = setBatchSize();
    thresh = setMaskThreshold();
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
        renameWindow(underscore_name + "-0001", number_name + "-Halo");
        renameWindow(underscore_name + "-0002", number_name + "-DAPI");
        
        runGaussianSubtraction(number_name + "-Halo");

        selectWindow("Result of 1");
        saveAs("Tiff", dest_directory + number_name + "_pre_threshold");

        generateMaximaMask(thresh);
        
        saveAs("Tiff", dest_directory + number_name + "_post_threshold");
        
        selectWindow(number_name + "-DAPI");
        resetMinAndMax();
        setAutoThreshold("Default dark");
        
        current_batch_count++;

        if (current_batch_count == images_per_batch) {
    		run("Tile");
    		run("Threshold...");
            waitForUser("Review image batch, then click OK to continue with the next batch.");
            current_batch_count = 0;
        }
    }
    run("Tile");
    run("Threshold...");
}

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

macro "RunThresholdTest" {
	file_path = File.openDialog("Choose Image");
	dir = File.getDirectory(file_path);
	
	file_name = File.getName(file_path);
	
	underscore_name = truncate(file_name, "_", 1);
	number_name = truncate(file_name, ".", 0);
	dest_directory = dir + number_name + "/";
	File.makeDirectory(dir + number_name);
	
	open(file_path);
	run("16-bit");
	
	source_file = dir + file_name;
	dest_file = dest_directory + file_name;			
	file_renamed = File.rename(source_file, dest_file);
	
	run("Stack to Images");
	
	renameWindow(underscore_name + "-0001", number_name + "-Halo");
	renameWindow(underscore_name + "-0002", number_name + "-DAPI");
	
	runGaussianSubtraction(number_name + "-Halo");

	selectWindow("Result of 1");
	saveAs("Tiff", dest_directory + number_name + "_pre_threshold");
	for (i = 10; i <= 100; i+=10) {
		selectWindow(number_name + "_pre_threshold.tif");
		run("Duplicate...", "title=dupe");
		generateMaximaMask(i);
		saveAs("Tiff", dest_directory + number_name + "_post_threshold" + i);
	}
	selectWindow(number_name + "-DAPI");
	resetMinAndMax();
	setAutoThreshold("Default dark");
	
	run("Analyze Particles...", "size=200-Infinity show=Outlines exclude include overlay add");
	close();
	saveAs("Tiff", dest_directory + number_name + "_nucleiROI");
	close();
	for (i = 10; i <= 100; i+=10) {
		selectWindow(number_name + "_post_threshold" + i + ".tif");
		run("From ROI Manager");
		run("Find Maxima...", "prominence=10 strict exclude output=[Single Points]");
		roiManager("Show All without labels");
		rename("Current Maxima" + number_name);
		roiManager("Measure");
		selectWindow(number_name + "_post_threshold" + i + ".tif");
		close();
		selectWindow("Current Maxima" + number_name);
		close();
		//close("Results");
		
		current_nRows = nResults; // Get number of rows in Results table
    	for (r = previous_nRows; r < current_nRows; r++) {
        	setResult("Threshold", r, i);
	        raw_intensity = getResult("RawIntDen", r);
	        foci_count = raw_intensity / 255;
	        setResult("NumFoci", r, foci_count);
	    }
	    updateResults();
	    previous_nRows = current_nRows;
	}
	
	selectWindow(number_name + "_pre_threshold.tif");
	close();
	
	saveAs("Results", dest_directory + number_name + "_results.csv");
	if (isOpen("Results")) {
		close("Results");
	}
	if (isOpen("ROI Manager")){
		close("ROI Manager");
	}
}	
	
