$(function () {
    $('.modal.addnew').on('click', '.btn-close', function () {
        $(this).closest('.modal').modal('hide')
    })

    $('table').on('click','.deleteItem', function() {
        var tr = $(this).closest('tr')[0]
        var data = {  objectId: $($(tr).find('td')[0]).text(),
                          type: $(tr).attr('object-type')
                   }
        $.post('deleteObject', data, function() {
            $(tr).remove()
        })


    })


    $('#saveContext').on('click', function() {
        var data = {            url: $('#addNewcontexts #url').val(),
                        displayName: $('#addNewcontexts #displayName').val(),
                     twitterHashtag: $('#addNewcontexts #twitterHashtag').val(),
                    twitterUsername: $('#addNewcontexts #twitterUsername').val(),
                               read: $('#addNewcontexts #read').val(),
                              write: $('#addNewcontexts #write').val(),
                               type: 'context'
                   }
        var modalForm = $(this).closest('.modal')[0]

        $.post('addNew', data, function() {
            $(modalForm).modal('hide')
        })
    })


    $('#saveUser').on('click', function() {
        var data = {       username: $('#addNewusers #username').val(),
                        displayName: $('#addNewusers #displayName').val(),
                               type: 'user'
                   }
        var modalForm = $(this).closest('.modal')[0]

        $.post('addNew', data, function() {
            $(modalForm).modal('hide')
        })
    })


})

