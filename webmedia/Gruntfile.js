module.exports = function(grunt) {
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        jshint: {
            files: ['Gruntfile.js', 'js/src/*.js'],
            options: {
                globals: {
                    jQuery: true,
                    console: true,
                    module: true
                },
                multistr: true
            }
        },
        concat: {
            dist: {
                src: ['js/src/*.js'],
                dest: 'js/build/<%= pkg.name %>.js'
            }
        }
    });

    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.registerTask('default', ['jshint', 'concat']);
};
