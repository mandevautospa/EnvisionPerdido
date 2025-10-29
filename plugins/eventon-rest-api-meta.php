<?php
/**
 * Plugin Name: EventON REST API Meta Fields
 * Description: Registers EventON custom meta fields with WordPress REST API
 * Version: 1.0
 * Author: Auto-generated for Community Calendar Integration
 * 
 * Installation:
 * 1. Save this file as: wp-content/plugins/eventon-rest-api-meta.php
 * 2. Log into WordPress admin
 * 3. Go to Plugins → Installed Plugins
 * 4. Find "EventON REST API Meta Fields" and click Activate
 * 5. Re-run your upload script
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Register EventON meta fields with REST API
 */
function register_eventon_meta_fields() {
    // List of EventON meta fields that need to be accessible via REST API
    $meta_fields = array(
        // Event date/time fields
        'evcal_srow',                 // Start timestamp
        'evcal_erow',                 // End timestamp
        'evcal_start_date',           // Start date (MM/DD/YYYY)
        'evcal_end_date',             // End date (MM/DD/YYYY)
        'evcal_start_time_hour',      // Start hour (12-hour format)
        'evcal_start_time_min',       // Start minute
        'evcal_start_time_ampm',      // AM/PM
        'evcal_end_time_hour',        // End hour
        'evcal_end_time_min',         // End minute
        'evcal_end_time_ampm',        // End AM/PM
        
        // Event settings
        'evcal_allday',               // All day event (yes/no)
        'evo_hide_endtime',           // Hide end time (yes/no)
        'evo_year_long',              // Year long event (yes/no)
        '_evcal_exlink_option',       // External link option
        
        // Event details
        'evcal_lmlink',               // Learn more link (URL)
        'evcal_location_name',        // Location name
        'evcal_location',             // Location details
        'event_location',             // Location taxonomy term ID
        'evcal_organizer',            // Organizer details
        'event_organizer',            // Organizer taxonomy term ID
        
        // Additional fields
        'evcal_subtitle',             // Event subtitle
        'evo_evcrd_field_org',        // Organizer info
        '_featured',                  // Featured event
        '_completed',                 // Event completed status
        '_cancel',                    // Event cancelled
    );
    
    // Register each meta field for the ajde_events post type
    foreach ($meta_fields as $field) {
        register_post_meta('ajde_events', $field, array(
            'show_in_rest' => true,
            'single' => true,
            'type' => 'string',
            'auth_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
    }
}

// Hook into REST API initialization
add_action('rest_api_init', 'register_eventon_meta_fields');

/**
 * Ensure meta fields are saved when creating/updating events via REST API
 */
function save_eventon_meta_on_rest_insert($post, $request, $creating) {
    // Only process ajde_events post type
    if ($post->post_type !== 'ajde_events') {
        return;
    }
    
    $meta = $request->get_param('meta');
    
    if (empty($meta) || !is_array($meta)) {
        return;
    }
    
    // Save each meta field
    foreach ($meta as $meta_key => $meta_value) {
        // Only save EventON-related fields
        if (strpos($meta_key, 'evcal_') === 0 || 
            strpos($meta_key, 'evo_') === 0 || 
            strpos($meta_key, 'event_') === 0 ||
            strpos($meta_key, '_evcal_') === 0 ||
            in_array($meta_key, ['_featured', '_completed', '_cancel'])) {
            
            update_post_meta($post->ID, $meta_key, sanitize_text_field($meta_value));
        }
    }
}

// Hook into post creation/update via REST API
add_action('rest_insert_ajde_events', 'save_eventon_meta_on_rest_insert', 10, 3);

/**
 * Log successful activation
 */
function eventon_rest_api_meta_activation() {
    error_log('EventON REST API Meta Fields plugin activated');
    
    // Flush rewrite rules to ensure REST API updates take effect
    flush_rewrite_rules();
}

register_activation_hook(__FILE__, 'eventon_rest_api_meta_activation');

/**
 * Add admin notice on activation
 */
function eventon_rest_api_meta_admin_notice() {
    $screen = get_current_screen();
    
    if ($screen && $screen->id === 'plugins') {
        ?>
        <div class="notice notice-success is-dismissible">
            <p><strong>EventON REST API Meta Fields</strong> is active! EventON metadata can now be saved via REST API.</p>
            <p>You can now run your event upload script to properly save event dates and metadata.</p>
        </div>
        <?php
    }
}

// Only show notice on first activation
if (get_transient('eventon_rest_api_meta_activated')) {
    add_action('admin_notices', 'eventon_rest_api_meta_admin_notice');
    delete_transient('eventon_rest_api_meta_activated');
}

register_activation_hook(__FILE__, function() {
    set_transient('eventon_rest_api_meta_activated', true, 5);
});
