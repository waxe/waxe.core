'use strict';

module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    // Metadata.
    pkg: grunt.file.readJSON('waxe.jquery.json'),
    banner: '/*! <%= pkg.title || pkg.name %> - v<%= pkg.version %> - ' +
      '<%= grunt.template.today("yyyy-mm-dd") %>\n' +
      '<%= pkg.homepage ? "* " + pkg.homepage + "\\n" : "" %>' +
      '* Copyright (c) <%= grunt.template.today("yyyy") %> <%= pkg.author.name %>;' +
      ' Licensed <%= _.pluck(pkg.licenses, "type").join(", ") %> */\n',
    // Task configuration.
    clean: {
      files: ['dist']
    },
    concat: {
      options: {
        banner: '<%= banner %>',
        stripBanners: true
      },
      dist: {
        src: [
            'libs/jquery/jquery.js',
            'libs/js/jquery-ui-1.10.1.custom.min.js',
            'libs/bootstrap-3.0.2/js/transition.js',
            'libs/bootstrap-3.0.2/js/alert.js',
            'libs/bootstrap-3.0.2/js/button.js',
            'libs/bootstrap-3.0.2/js/carousel.js',
            'libs/bootstrap-3.0.2/js/collapse.js',
            'libs/bootstrap-3.0.2/js/dropdown.js',
            'libs/bootstrap-3.0.2/js/modal.js',
            'libs/bootstrap-3.0.2/js/tooltip.js',
            'libs/bootstrap-3.0.2/js/popover.js',
            'libs/bootstrap-3.0.2/js/scrollspy.js',
            'libs/bootstrap-3.0.2/js/tab.js',
            'libs/bootstrap-3.0.2/js/affix.js',
            'libs/js/jquery.layout-latest.min.js',
            'libs/js/jquery.message.js',
            'libs/js/jquery.autosize.js',
            'libs/codemirror/codemirror.js',
            'libs/codemirror/xml.js',
            'bower_components/jquery.contenteditablesync/src/*.js',
            'src/jquery.filebrowser.js',
            'src/ajax.js',
            'src/event.js',
            'src/layout.js',
            'src/form.js',
            'src/utils.js',
            'src/dom.js',
            'src/jquery.filebrowser.js',
            'src/navbar.js',
            'src/versioning.js',
            'src/plugins-options.js',
            'src/window.js',
        ],
        dest: '../waxe/core/static/js/<%= pkg.name %>.js'
      }
    },
    uglify: {
      options: {
        banner: '<%= banner %>'
      },
      dist: {
        src: '<%= concat.dist.dest %>',
        dest: '../waxe/core/static/js/<%= pkg.name %>.min.js'
      },
    },
    qunit: {
      files: ['test/**/*.html']
    },
    jshint: {
      gruntfile: {
        options: {
          jshintrc: '.jshintrc'
        },
        src: 'Gruntfile.js'
      },
      src: {
        options: {
          jshintrc: 'src/.jshintrc'
        },
        src: ['src/**/*.js']
      },
      test: {
        options: {
          jshintrc: 'test/.jshintrc'
        },
        src: ['test/**/*.js']
      },
    },
    less: {
        development: {
            options: {
                paths: ['libs/bootstrap-3.0.2/less/']
            },
            files: {
                "../waxe/core/static/css/<%= pkg.name %>.css": [
                    "css/*.less",
                    "libs/codemirror/codemirror.css"
                ]
            }
        },
        production: {
            options: {
                paths: ['libs/bootstrap-3.0.2/less/'],
                cleancss: true
            },
            files: {
                "../waxe/core/static/css/<%= pkg.name %>.min.css": [
                    "css/*.less",
                    "libs/codemirror/codemirror.css"
                ]
            }
        }
    },
    copy: {
        main: {
            files: [
                {
                    expand: true,
                    cwd: 'libs/bootstrap-3.0.2/fonts',
                    src: ['*'],
                    dest: '../waxe/core/static/fonts/'
                },
                // Improve this rules to only copy needed files
                {
                    expand: true,
                    cwd: 'bower_components/bootstrap/',
                    src: ['**'],
                    dest: '../waxe/core/static/bootstrap/'
                },
                {
                    expand: true,
                    cwd: 'bower_components/ckeditor/',
                    src: ['**'],
                    dest: '../waxe/core/static/ckeditor/'
                },
                {
                    expand: true,
                    cwd: 'bower_components/font-awesome/',
                    src: ['**'],
                    dest: '../waxe/core/static/font-awesome/'
                }
            ]
        }
    },
    watch: {
      gruntfile: {
        files: '<%= jshint.gruntfile.src %>',
        tasks: ['jshint:gruntfile']
      },
      src: {
        files: '<%= jshint.src.src %>',
        tasks: ['jshint:src', 'qunit']
      },
      test: {
        files: '<%= jshint.test.src %>',
        tasks: ['jshint:test', 'qunit']
      },
    },
  });

  // These plugins provide necessary tasks.
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-qunit');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-contrib-copy');

  // Default task.
  grunt.registerTask('default', ['jshint', 'clean', 'concat', 'uglify', 'less', 'copy']);
  grunt.registerTask('js', ['jshint', 'concat', 'uglify']);
  grunt.registerTask('css', ['less']);
};
